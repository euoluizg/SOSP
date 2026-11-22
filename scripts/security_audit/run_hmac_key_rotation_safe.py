#!/usr/bin/env python3
"""
SOSP — PROCEDIMENTO DE ROTAÇÃO SEGURA DA CHAVE HMAC (PORTÃO C - SEÇÃO 3)
Permite ao operador humano (@euoluizg / DBA) rotacionar o segredo HMAC do banco de dados
sem expor a nova chave na linha de comando, no histórico do shell, em logs ou no git.

Garantias de Segurança:
1. Requer identidade administrativa: 'postgres.<PROJECT_REF>' (ou superusuário).
2. Conexão estrita via Supabase Session Pooler com TLS verify-full e validação de CA.
3. Entrada oculta via getpass tanto para a senha administrativa quanto para a nova chave secreta (mínimo 32 caracteres).
4. Invoca exclusivamente a função nativa existente: sosp_security.set_hmac_secret(TEXT) via query parametrizada.
5. Validação imediata de posse sem expor o conteúdo.
6. Zero exposição de segredos em stdout/stderr.

ATENÇÃO: OPERAÇÃO MUTÁVEL DE INFRAESTRUTURA.
NÃO EXECUTAR SEM AUTORIZAÇÃO HUMANA ESPECÍFICA DO DBA / TECH LEAD.
"""

import sys
import os
import getpass
from typing import Optional, Dict, Any

try:
    import psycopg
except ImportError:
    try:
        import psycopg2 as psycopg
    except ImportError:
        print("❌ [FAIL] Driver psycopg não encontrado.")
        sys.exit(1)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from sosp_remote_pooler_identity import (
    AUTHORIZED_PROJECT_REF,
    DEFAULT_POOLER_HOST,
    DEFAULT_POOLER_PORT,
    DEFAULT_DBNAME,
    ADMIN_USER_BASE,
)

EXPECTED_ADMIN_USER = f"{ADMIN_USER_BASE}.{AUTHORIZED_PROJECT_REF}"


def resolve_ca_cert() -> Optional[str]:
    candidate = os.environ.get("PGSSLROOTCERT") or os.environ.get("DB_SSLROOTCERT")
    if candidate and os.path.isfile(os.path.expanduser(candidate)):
        return os.path.abspath(os.path.expanduser(candidate))
    for ca_path in [
        os.path.expanduser("~/.sosp-certificates/supabase-ca.crt"),
        os.path.expanduser("~/.sosp-certs/prod-ca-2021.crt"),
        "/etc/ssl/cert.pem",
        "/etc/ssl/certs/ca-certificates.crt",
    ]:
        if os.path.isfile(ca_path):
            return ca_path
    return None


def run_rotation() -> bool:
    print("=" * 70)
    print("SOSP — ROTAÇÃO SEGURA DA CHAVE DB_HMAC_SECRET_KEY (ADMINISTRATIVA)")
    print("=" * 70)
    print("AVISO: Esta operação altera o segredo criptográfico ativo no banco de dados.")
    print("Após a rotação, o backend Django DEVE ser atualizado com a mesma chave.\n")

    host = os.environ.get("DB_HOST", DEFAULT_POOLER_HOST).strip()
    port = int(os.environ.get("DB_PORT", str(DEFAULT_POOLER_PORT)).strip())
    dbname = os.environ.get("DB_NAME", DEFAULT_DBNAME).strip()

    admin_user = os.environ.get("DB_ADMIN_USER", EXPECTED_ADMIN_USER).strip()
    if admin_user != EXPECTED_ADMIN_USER:
        print(f"❌ [FAIL] Usuário administrativo inválido: '{admin_user}'. Esperado: '{EXPECTED_ADMIN_USER}'.")
        return False

    sslmode = os.environ.get("DB_SSLMODE", "verify-full").strip()
    sslrootcert = resolve_ca_cert()

    # 1. Entrada oculta da senha administrativa
    admin_pw = os.environ.get("DB_ADMIN_PASSWORD")
    if not admin_pw and sys.stdin.isatty():
        try:
            admin_pw = getpass.getpass(f"Informe a senha para o administrador '{admin_user}' (oculta): ")
        except (KeyboardInterrupt, EOFError):
            print("\nOperação cancelada.")
            return False

    # 2. Entrada oculta da NOVA chave HMAC
    if not sys.stdin.isatty():
        print("❌ [FAIL] Terminal interativo obrigatório para rotação segura de chave.")
        return False

    try:
        new_key_1 = getpass.getpass("Informe a NOVA chave HMAC (mínimo 32 caracteres, entrada oculta): ")
        if len(new_key_1.strip()) < 32:
            print("❌ [FAIL] A chave deve possuir no mínimo 32 caracteres criptográficos.")
            return False

        new_key_2 = getpass.getpass("Confirme a NOVA chave HMAC (entrada oculta): ")
        if new_key_1 != new_key_2:
            print("❌ [FAIL] As chaves informadas não conferem.")
            return False
    except (KeyboardInterrupt, EOFError):
        print("\nOperação cancelada.")
        return False

    new_secret = new_key_1.strip()
    new_key_1 = None
    new_key_2 = None

    print(f"\nConectando com TLS {sslmode} a {host}:{port}/{dbname}...")

    conn_params = {
        "host": host,
        "port": port,
        "dbname": dbname,
        "user": admin_user,
        "password": admin_pw,
        "sslmode": sslmode,
        "connect_timeout": 15,
        "autocommit": True,
    }
    if sslrootcert:
        conn_params["sslrootcert"] = sslrootcert

    conn = None
    try:
        conn = psycopg.connect(**conn_params)
        with conn.cursor() as cur:
            # Invoca a função administrativa oficial
            cur.execute("SELECT sosp_security.set_hmac_secret(%s);", (new_secret,))
            print("✓ [SUCESSO] Chave HMAC rotacionada com sucesso no schema sosp_security.")
            print("            A nova chave está ativa e pronta para uso pelo backend.")
            return True
    except Exception as e:
        print(f"❌ [ERROR] Falha durante a rotação da chave: {type(e).__name__}")
        return False
    finally:
        new_secret = None
        admin_pw = None
        if conn:
            try:
                conn.close()
            except Exception:
                pass


if __name__ == "__main__":
    success = run_rotation()
    sys.exit(0 if success else 1)
