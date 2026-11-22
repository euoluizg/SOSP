#!/usr/bin/env python3
"""
SOSP — PORTÃO C.2: VALIDAÇÃO CRIPTOGRÁFICA DO CONTEXTO HMAC (OPERAÇÃO MUTÁVEL)
Comprova a compatibilidade criptográfica entre a chave configurada no backend e o segredo
ativo armazenado no schema sosp_security do PostgreSQL remoto.

AVISO DE SEGURANÇA E TRANSAÇÃO:
1. Esta operação é MUTÁVEL caso seja commitada, pois grava 1 registro em 'sosp_security.used_nonces'.
2. Se executada com ROLLBACK, a aceitação criptográfica é comprovada em voo, mas o consumo do nonce é desfeito.
3. Utiliza exclusivamente a identidade de runtime: 'sosp_runtime_app.<PROJECT_REF>'.
4. A chave HMAC e as senhas são solicitadas exclusivamente via getpass (entrada oculta).
5. Zero exposição de segredos em logs, histórico de shell ou saída do terminal.

ATENÇÃO: NÃO EXECUTAR REMOTAMENTE SEM AUTORIZAÇÃO HUMANA ESPECÍFICA DO TECH LEAD / DBA.
"""

import sys
import os
import uuid
import time
import hmac
import hashlib
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
    RUNTIME_ROLE,
)

EXPECTED_RUNTIME_USER = f"{RUNTIME_ROLE}.{AUTHORIZED_PROJECT_REF}"


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


def run_gate_c2_hmac() -> bool:
    print("=" * 70)
    print("SOSP — PORTÃO C.2: VALIDAÇÃO CRIPTOGRÁFICA DO CONTEXTO HMAC")
    print("=" * 70)
    print("⚠️  AVISO OPERACIONAL: Esta operação valida a posse da chave HMAC e pode")
    print("    gravar 1 registro (nonce) na tabela 'sosp_security.used_nonces'.")
    print("    Exige autorização humana específica do operador responsável.\n")

    host = os.environ.get("DB_HOST", DEFAULT_POOLER_HOST).strip()
    port = int(os.environ.get("DB_PORT", str(DEFAULT_POOLER_PORT)).strip())
    dbname = os.environ.get("DB_NAME", DEFAULT_DBNAME).strip()

    # 1. Validação estrita de identidade de runtime
    user_env = os.environ.get("DB_USER") or os.environ.get("PGUSER")
    candidate = (user_env or "").strip()
    if host == DEFAULT_POOLER_HOST:
        if not candidate:
            candidate = EXPECTED_RUNTIME_USER
        if "postgres" in candidate.lower() or "admin" in candidate.lower():
            print(f"❌ [FAIL] Violação: Usuário administrativo '{candidate}' rejeitado no Portão C.2.")
            return False
        if candidate != EXPECTED_RUNTIME_USER:
            print(f"❌ [FAIL] Usuário incorreto '{candidate}'. Esperado: '{EXPECTED_RUNTIME_USER}'.")
            return False
        user = candidate
    else:
        user = candidate or RUNTIME_ROLE

    print(f"✓ Identidade de runtime validada: '{user}'")

    sslmode = os.environ.get("DB_SSLMODE", "verify-full" if host == DEFAULT_POOLER_HOST else "prefer").strip()
    sslrootcert = resolve_ca_cert()
    if sslrootcert:
        print(f"✓ Certificado CA: '{sslrootcert}'")

    # 2. Confirmação do operador humano
    if sys.stdin.isatty():
        try:
            confirm = input("Confirmar execução do Portão C.2 contra o banco de dados? (sim/NÃO): ").strip().lower()
            if confirm not in ("sim", "s", "yes", "y"):
                print("Operação abortada pelo operador.")
                return False
        except (KeyboardInterrupt, EOFError):
            print("\nOperação cancelada.")
            return False

    # 3. Solicitação protegida da senha de runtime e da chave HMAC
    password = os.environ.get("DB_PASSWORD") or os.environ.get("PGPASSWORD")
    if not password and sys.stdin.isatty():
        try:
            password = getpass.getpass(f"Informe a senha para '{user}' (oculta): ")
        except (KeyboardInterrupt, EOFError):
            print("\nOperação cancelada.")
            return False

    hmac_key = os.environ.get("DB_HMAC_SECRET_KEY")
    if not hmac_key and sys.stdin.isatty():
        try:
            hmac_key = getpass.getpass("Informe a chave DB_HMAC_SECRET_KEY para teste de posse (oculta): ")
        except (KeyboardInterrupt, EOFError):
            print("\nOperação cancelada.")
            return False

    if not hmac_key or len(hmac_key.strip()) < 32:
        print("❌ [FAIL] Chave HMAC inválida ou menor que 32 caracteres.")
        return False

    clean_hmac = hmac_key.strip()
    hmac_key = None

    # 4. Geração do Payload de Teste Criptográfico Efêmero
    test_user_id = str(uuid.uuid4())
    test_role = "citizen"
    test_agency = ""
    now_epoch = int(time.time())
    expires_at = now_epoch + 60
    test_nonce = str(uuid.uuid4())

    # Formato canônico: uid:role:agency:exp:nonce
    payload = f"{test_user_id}:{test_role}:{test_agency}:{expires_at}:{test_nonce}".encode("utf-8")
    sig = hmac.new(clean_hmac.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    conn_params = {
        "host": host,
        "port": port,
        "dbname": dbname,
        "user": user,
        "password": password,
        "sslmode": sslmode,
        "connect_timeout": 15,
        "autocommit": False,
    }
    if sslrootcert:
        conn_params["sslrootcert"] = sslrootcert

    conn = None
    try:
        print(f"\nConectando a {host}:{port}/{dbname}...")
        conn = psycopg.connect(**conn_params)
        with conn.cursor() as cur:
            # Invoca set_request_context
            cur.execute(
                "SELECT sosp_security.set_request_context(%s, %s, %s, %s, %s, %s);",
                (test_user_id, test_role, None, expires_at, test_nonce, sig)
            )
            success = cur.fetchone()[0]
            if not success:
                print("❌ [FAIL] Assinatura HMAC rejeitada pelo PostgreSQL remoto.")
                print("         A chave informada difere do segredo ativo em 'sosp_security.hmac_secret'.")
                conn.rollback()
                return False

            # Valida contexto ativo
            cur.execute("SELECT sosp_security.is_context_valid();")
            is_valid = cur.fetchone()[0]
            assert is_valid is True, "Contexto deveria estar válido."

            # Limpa contexto para manter higiene de pool
            cur.execute("SELECT sosp_security.clear_request_context();")

            # Comita para persistir o consumo do nonce e provar anti-replay
            conn.commit()

            print("✓ [SUCESSO] Assinatura HMAC aceita com sucesso pelo schema sosp_security!")
            print("            Compatibilidade criptográfica entre backend e PostgreSQL comprovada.")
            print("            1 Nonce unívoco consumido e registrado com sucesso em 'sosp_security.used_nonces'.")

            # -----------------------------------------------------------------
            # TESTE DE ANTI-REPLAY: Rejeição imediata de reuso do mesmo nonce
            # -----------------------------------------------------------------
            cur.execute(
                "SELECT sosp_security.set_request_context(%s, %s, %s, %s, %s, %s);",
                (test_user_id, test_role, None, expires_at, test_nonce, sig)
            )
            replay_res = cur.fetchone()[0]
            if replay_res is not False:
                print("❌ [FAIL] Falha de segurança: Nonce reutilizado não foi rejeitado pelo Anti-Replay!")
                cur.execute("SELECT sosp_security.clear_request_context();")
                conn.rollback()
                return False

            cur.execute("SELECT sosp_security.clear_request_context();")
            conn.rollback()
            print("✓ [ANTI-REPLAY] Reutilização do mesmo nonce sumariamente bloqueada pelo banco (False).")
            return True

    except Exception as e:
        print(f"❌ [ERROR] Falha durante a validação HMAC: {type(e).__name__}")
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        return False
    finally:
        clean_hmac = None
        sig = None
        payload = None
        if conn:
            try:
                conn.close()
            except Exception:
                pass


if __name__ == "__main__":
    success = run_gate_c2_hmac()
    sys.exit(0 if success else 1)
