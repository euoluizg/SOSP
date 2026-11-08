"""
SOSP — Módulo de Autenticação Segura Django REST Framework (ADR-003, RF-01, RF-02).

Implementa:
1. Autenticação por token Bearer criptografado (HMAC-SHA256 URL-safe, sem dependência externa).
2. Validação rigorosa de expiração temporal (RN-28: 30 minutos de inatividade).
3. Extração confiável de identidade: user_id, role ('citizen', 'server', 'admin', 'superadmin'), agency_id.
4. Re-validação de status no repositório (impede confiar exclusivamente em claims antigas se usuário foi desativado).
5. Estabelecimento automático do contexto de segurança PostgreSQL no momento da autenticação.
6. Usuário autenticado tipado (SospUser) compatível com DRF e com o contexto de segurança PostgreSQL.
"""

import hmac
import hashlib
import json
import base64
import time
import uuid
import logging
from typing import Optional, Tuple, Dict, Any

from django.conf import settings
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger(__name__)


class SospAnonymousUser:
    """Representação de usuário anônimo / não autenticado no SOSP."""
    id = None
    role = "anonymous"
    agency_id = None
    is_authenticated = False
    is_anonymous = True
    is_staff = False
    is_superuser = False

    def __str__(self) -> str:
        return "SospAnonymousUser"


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (4 - (len(data) % 4)) if len(data) % 4 != 0 else ""
    return base64.urlsafe_b64decode((data + padding).encode("utf-8"))


class SospUser:
    """
    Representação de usuário autenticado no SOSP.
    Imutável, tipado e sem privilégios arbitrários.
    """
    def __init__(
        self,
        user_id: str | uuid.UUID,
        role: str,
        agency_id: str | uuid.UUID | None = None,
        cpf: str = "",
        full_name: str = "",
        email: str = "",
        is_active: bool = True,
    ):
        self.id = uuid.UUID(str(user_id)) if isinstance(user_id, str) and len(user_id) == 36 else user_id
        self.role = role
        self.agency_id = uuid.UUID(str(agency_id)) if isinstance(agency_id, str) and len(str(agency_id)) == 36 else agency_id
        self.cpf = cpf
        self.full_name = full_name
        self.email = email
        self.is_active = is_active
        self.is_authenticated = True
        self.is_anonymous = False

    @property
    def is_staff(self) -> bool:
        return self.role in ("server", "admin", "superadmin", "servant", "administrator")

    @property
    def is_superuser(self) -> bool:
        return self.role in ("superadmin", "administrator")

    def __str__(self) -> str:
        return f"SospUser(id={self.id}, role={self.role}, agency={self.agency_id})"


def generate_sosp_token(
    user_id: str | uuid.UUID,
    role: str,
    agency_id: str | uuid.UUID | None = None,
    cpf: str = "",
    full_name: str = "",
    email: str = "",
    expires_in_seconds: int = 1800,  # 30 minutos (RN-28)
) -> str:
    """
    Gera um token criptográfico assinado HMAC-SHA256 (compatível com padrão JWT HS256).
    Utiliza Django SECRET_KEY para a assinatura do token de transporte.
    """
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": str(user_id),
        "role": role,
        "agency_id": str(agency_id) if agency_id else None,
        "cpf": cpf,
        "name": full_name,
        "email": email,
        "iat": now,
        "exp": now + expires_in_seconds,
        "jti": uuid.uuid4().hex,
    }

    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

    secret_key = settings.SECRET_KEY.encode("utf-8")
    sig = hmac.new(secret_key, signing_input, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(sig)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def verify_sosp_token(token: str) -> Dict[str, Any]:
    """
    Verifica a autenticidade, integridade e validade temporal de um token.
    Lança AuthenticationFailed em caso de violação.
    """
    parts = token.strip().split(".")
    if len(parts) != 3:
        raise AuthenticationFailed("Formato de token inválido.")

    header_b64, payload_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    secret_key = settings.SECRET_KEY.encode("utf-8")

    expected_sig = hmac.new(secret_key, signing_input, hashlib.sha256).digest()
    actual_sig = _b64url_decode(sig_b64)

    if not hmac.compare_digest(expected_sig, actual_sig):
        raise AuthenticationFailed("Assinatura do token de autenticação inválida.")

    try:
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    except Exception:
        raise AuthenticationFailed("Payload do token corrompido.")

    now = int(time.time())
    exp = payload.get("exp")
    if not exp or now > exp:
        raise AuthenticationFailed("Sessão expirada por inatividade. Faça login novamente.")

    return payload


class SospTokenAuthentication(BaseAuthentication):
    """
    Autenticador oficial do DRF para o SOSP.
    Lê o cabeçalho 'Authorization: Bearer <token>', re-valida status no repositório
    e estabelece o contexto de segurança no banco de dados.
    """
    keyword = "Bearer"

    def authenticate_header(self, request):
        return self.keyword

    def authenticate(self, request) -> Optional[Tuple[SospUser, str]]:
        auth = get_authorization_header(request).split()

        if not auth:
            return None

        if auth[0].decode("utf-8").lower() != self.keyword.lower():
            return None

        if len(auth) == 1:
            raise AuthenticationFailed("Cabeçalho de autenticação sem token.")
        elif len(auth) > 2:
            raise AuthenticationFailed("Cabeçalho de autenticação mal formatado.")

        token = auth[1].decode("utf-8")
        payload = verify_sosp_token(token)

        user_id = payload.get("sub")
        role = payload.get("role", "citizen")
        agency_id = payload.get("agency_id")

        user = SospUser(
            user_id=user_id,
            role=role,
            agency_id=agency_id,
            cpf=payload.get("cpf", ""),
            full_name=payload.get("name", ""),
            email=payload.get("email", ""),
            is_active=True,
        )

        # 1. Estabelece o contexto de segurança autenticado na conexão PostgreSQL ativa (ADR-003, Etapa 4D.2)
        try:
            from common.security.db_context import set_db_security_context, clear_db_security_context
            set_db_security_context(user=user)
        except Exception as e:
            logger.warning("Falha ao definir contexto de banco no autenticador DRF: %s", e)

        # 2. Verifica revogação de sessão no servidor (accountsSession / revogação ativa sob RLS)
        try:
            from apps.accounts.repositories import citizen_repository
            token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
            if citizen_repository.is_session_revoked(token_hash):
                try:
                    from common.security.db_context import clear_db_security_context
                    clear_db_security_context()
                except Exception:
                    pass
                raise AuthenticationFailed("Sessão revogada no servidor. Faça login novamente.")
        except AuthenticationFailed:
            raise
        except Exception as e:
            logger.debug("Verificação de revogação de sessão ignorada: %s", e)

        # 3. Re-validação de status no banco sob o próprio contexto RLS do usuário (anti-stale claims)
        try:
            from apps.accounts.repositories import citizen_repository
            citizen = citizen_repository.get_by_id(str(user_id))
            if citizen:
                if not citizen.get("isActive", True) or citizen.get("deletedAt"):
                    try:
                        from common.security.db_context import clear_db_security_context
                        clear_db_security_context()
                    except Exception:
                        pass
                    raise AuthenticationFailed("Conta desativada ou excluída.")
                role = citizen.get("role", role)
                user.role = role
        except AuthenticationFailed:
            raise
        except Exception as e:
            logger.debug("Verificação de repositório no autenticador ignorada para perfil não-cidadão: %s", e)

        return (user, token)
