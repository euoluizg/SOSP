"""
Módulo de Segurança de Contexto PostgreSQL do SOSP (ADR-001, ADR-003, Etapa 4D.2).

Implementa:
1. Geração de assinaturas HMAC-SHA256 para contexto transacional com expiração temporal e Nonce de uso único (Anti-Replay estrito entre transações).
2. Definição segura do contexto na transação via função SECURITY DEFINER sosp_security.set_request_context.
3. Limpeza obrigatória do contexto (clear_request_context) no encerramento de requisição/transação para impedir reaproveitamento de conexão no pool.
4. Isolamento estrito entre Django SECRET_KEY e DB_HMAC_SECRET_KEY.
5. Integração com o ciclo de vida do DRF (SospSecurityContextMixin) garantindo estabelecimento pós-autenticação.
"""

import hmac
import hashlib
import time
import os
import uuid
import logging
from contextlib import contextmanager
from typing import Optional, Any

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import connection as default_connection

logger = logging.getLogger(__name__)


def get_db_hmac_secret_key() -> str:
    """
    Retorna a chave HMAC exclusiva do banco de dados (diferente de Django SECRET_KEY).
    Falha explicitamente se ausente quando REPOSITORY_BACKEND == 'orm'.
    """
    key = getattr(settings, "DB_HMAC_SECRET_KEY", None) or os.environ.get("DB_HMAC_SECRET_KEY")
    if not key:
        repository_backend = getattr(settings, "REPOSITORY_BACKEND", "memory")
        if repository_backend == "orm":
            raise ImproperlyConfigured(
                "DB_HMAC_SECRET_KEY não foi configurada. Em modo 'orm', uma chave HMAC "
                "de no mínimo 32 caracteres é obrigatória para proteção de contexto RLS."
            )
        # Em modo memory / teste sem banco real, gera chave dummy efêmera
        return "sosp_local_dummy_hmac_secret_key_32b_ok"
    if len(key.strip()) < 32:
        raise ImproperlyConfigured("DB_HMAC_SECRET_KEY deve possuir no mínimo 32 caracteres criptográficos.")
    return key.strip()


def compute_context_hmac(
    user_id: str | uuid.UUID | None,
    role: str,
    agency_id: str | uuid.UUID | None,
    expires_at: int,
    nonce: str | uuid.UUID | None = None,
    secret_key: str | None = None,
) -> str:
    """
    Calcula o HMAC-SHA256 idêntico ao validado pela rotina sosp_security.set_request_context.
    Inclui o nonce na assinatura para garantir unicidade e proteção anti-replay estrita.
    """
    key = secret_key or get_db_hmac_secret_key()
    uid_str = str(user_id) if user_id else ""
    aid_str = str(agency_id) if agency_id else ""
    nonce_str = str(nonce) if nonce else ""
    payload = f"{uid_str}:{role}:{aid_str}:{expires_at}:{nonce_str}".encode("utf-8")
    return hmac.new(key.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def set_db_security_context(
    conn=None,
    user=None,
    nonce: str | uuid.UUID | None = None,
    expires_in_seconds: int = 60,
) -> bool:
    """
    Define o contexto de segurança na conexão PostgreSQL ativa.
    Se o banco não for PostgreSQL ou REPOSITORY_BACKEND == 'memory', no-op seguro.
    """
    active_conn = conn or default_connection
    if active_conn.vendor != "postgresql":
        return True

    now_epoch = int(time.time())
    expires_at = now_epoch + max(5, min(expires_in_seconds, 120))
    req_nonce = str(nonce or uuid.uuid4())

    if user and getattr(user, "is_authenticated", False):
        user_id = getattr(user, "id", None)
        raw_role = getattr(user, "role", "citizen")
        if raw_role in ("server", "servant", "servidor", "gestor", "manager", "internal"):
            role = "server"
        elif raw_role in ("admin", "superadmin", "administrador"):
            role = "admin" if raw_role == "admin" else "superadmin"
        else:
            role = "citizen"
        agency_id = getattr(user, "agency_id", None)
    else:
        user_id = None
        role = "anonymous"
        agency_id = None

    sig = compute_context_hmac(user_id, role, agency_id, expires_at, req_nonce)

    with active_conn.cursor() as cursor:
        cursor.execute(
            "SELECT sosp_security.set_request_context(%s, %s, %s, %s, %s, %s);",
            (user_id, role, agency_id, expires_at, req_nonce, sig),
        )
        row = cursor.fetchone()
        success = row[0] if row else False
        if not success:
            logger.warning("Falha ao definir contexto de segurança PostgreSQL para user_id=%s, role=%s", user_id, role)
        return bool(success)


def clear_db_security_context(conn=None) -> None:
    """Limpa o contexto de segurança, impedindo contaminação no pooler de conexões."""
    active_conn = conn or default_connection
    if active_conn.vendor != "postgresql":
        return

    try:
        with active_conn.cursor() as cursor:
            cursor.execute("SELECT sosp_security.clear_request_context();")
    except Exception as e:
        logger.warning("Falha ao limpar contexto de segurança PostgreSQL: %s", e)


@contextmanager
def db_security_context(user=None, conn=None, nonce: str | uuid.UUID | None = None, expires_in_seconds: int = 60):
    """Context manager para delimitar transações e operações sob contexto seguro."""
    active_conn = conn or default_connection
    set_db_security_context(active_conn, user, nonce, expires_in_seconds)
    try:
        yield
    finally:
        clear_db_security_context(active_conn)


class SospSecurityContextMixin:
    """
    Mixin para APIViews do Django REST Framework.
    Garante que o contexto PostgreSQL seja estabelecido APÓS a autenticação da view
    e limpo com garantia absoluta em finalize_response.
    """
    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        # Neste ponto, perform_authentication já foi executado pelo DRF
        set_db_security_context(user=request.user)

    def finalize_response(self, request, response, *args, **kwargs):
        try:
            return super().finalize_response(request, response, *args, **kwargs)
        finally:
            clear_db_security_context()


class SospDatabaseSecurityContextMiddleware:
    """
    Middleware Django de contenção de borda.
    Garante limpeza de contexto mesmo em casos de exceções precoces fora do DRF
    (ex: falhas em middlewares anteriores, timeouts, conexões canceladas).
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        finally:
            clear_db_security_context()
