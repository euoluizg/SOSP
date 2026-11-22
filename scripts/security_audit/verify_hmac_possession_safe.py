#!/usr/bin/env python3
"""
SOSP — Verificação Segura de Posse de HMAC (Zero-Leakage)
Valida criptograficamente que o segredo DB_HMAC_SECRET_KEY configurado na aplicação
corresponde ao segredo ativo armazenado no schema sosp_security.hmac_secret do PostgreSQL,
sem expor, imprimir, registrar ou aceitar a chave via argumentos de linha de comando.
"""

import sys
import os
import uuid
import time
import hmac
import hashlib
import getpass
from typing import Optional

try:
    import psycopg
except ImportError:
    try:
        import psycopg2 as psycopg
    except ImportError:
        print("[FAIL] Módulo psycopg ou psycopg2 não encontrado no ambiente Python.")
        sys.exit(1)


def get_hmac_key_securely() -> Optional[str]:
    """
    Obtém a chave HMAC de forma estritamente segura:
    1. Variável de ambiente DB_HMAC_SECRET_KEY (injetada de forma protegida).
    2. Entrada protegida e oculta via getpass no terminal interativo.
    PROIBIDO: Leitura via argumentos de linha de comando (sys.argv).
    """
    # 1. Verifica se foi passada indevidamente via CLI e aborta
    for arg in sys.argv[1:]:
        if "--hmac" in arg or "--key" in arg or "--secret" in arg:
            print("[SECURITY ERROR] Chaves secretas jamais devem ser passadas via linha de comando.")
            sys.exit(1)

    key = os.environ.get("DB_HMAC_SECRET_KEY")
    if key and len(key.strip()) >= 32:
        return key.strip()

    if sys.stdin.isatty():
        try:
            prompted = getpass.getpass("Informe a chave DB_HMAC_SECRET_KEY (entrada oculta): ")
            if prompted and len(prompted.strip()) >= 32:
                return prompted.strip()
            print("[FAIL] A chave informada deve possuir no mínimo 32 caracteres criptográficos.")
            return None
        except (KeyboardInterrupt, EOFError):
            print("\nOperação cancelada pelo usuário.")
            return None

    print("[FAIL] DB_HMAC_SECRET_KEY não encontrada no ambiente e terminal não é interativo.")
    return None


def verify_hmac_possession() -> bool:
    hmac_key = get_hmac_key_securely()
    if not hmac_key:
        return False

    host = os.environ.get("DB_HOST", "127.0.0.1")
    port = int(os.environ.get("DB_PORT", "5432"))
    dbname = os.environ.get("DB_NAME", "postgres")
    user = os.environ.get("DB_USER", "postgres")
    password = os.environ.get("DB_PASSWORD") or os.environ.get("PGPASSWORD")
    sslmode = os.environ.get("DB_SSLMODE", "prefer")
    sslrootcert = os.environ.get("DB_SSLROOTCERT") or os.environ.get("PGSSLROOTCERT")
    if not sslrootcert or not os.path.isfile(os.path.expanduser(sslrootcert)):
        for ca_path in [
            os.path.expanduser("~/.sosp-certificates/supabase-ca.crt"),
            os.path.expanduser("~/.sosp-certs/prod-ca-2021.crt"),
            "/etc/ssl/cert.pem",
            "/etc/ssl/certs/ca-certificates.crt",
        ]:
            if os.path.isfile(ca_path):
                sslrootcert = ca_path
                break

    if host not in ("127.0.0.1", "localhost") and sslmode != "verify-full":
        print(f"[WARN] Conexão com host remoto '{host}' deve utilizar preferencialmente 'sslmode=verify-full'.")

    print("\nAVISO OPERACIONAL: Esta validação criptográfica CONSOME 1 NONCE na tabela sosp_security.used_nonces.")
    print("Portanto, NÃO é uma operação estritamente read-only (pertence ao Portão C.2, não ao Portão A).")

    if not password and sys.stdin.isatty() and host not in ("127.0.0.1", "localhost"):
        try:
            password = getpass.getpass(f"Informe a senha para o usuário {user} (oculta): ")
        except (KeyboardInterrupt, EOFError):
            print("\nOperação cancelada.")
            return False

    # Gera contexto de teste efêmero estritamente compatível com sosp_security.set_request_context
    test_user_id = uuid.uuid4()
    test_role = "citizen"
    test_agency_id = None
    now_epoch = int(time.time())
    expires_at = now_epoch + 60
    test_nonce = uuid.uuid4()

    # Formato canônico: uid:role:agency:expires:nonce
    payload = f"{test_user_id}:{test_role}::{expires_at}:{test_nonce}".encode("utf-8")
    signature = hmac.new(hmac_key.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    conn_params = {
        "host": host,
        "port": port,
        "dbname": dbname,
        "user": user,
        "password": password,
        "sslmode": sslmode,
        "connect_timeout": 15,
    }
    if sslrootcert and os.path.isfile(sslrootcert):
        conn_params["sslrootcert"] = sslrootcert

    conn = None
    try:
        conn = psycopg.connect(**conn_params)
        with conn.cursor() as cur:
            # 1. Testa definição de contexto no schema sosp_security
            cur.execute("""
                SELECT sosp_security.set_request_context(%s, %s, %s, %s, %s, %s);
            """, (
                test_user_id,
                test_role,
                test_agency_id,
                expires_at,
                test_nonce,
                signature
            ))
            row = cur.fetchone()
            is_valid = bool(row[0]) if row else False

            # 2. Limpa imediatamente o contexto para evitar contaminação
            cur.execute("SELECT sosp_security.clear_request_context();")
            conn.commit()

            if is_valid:
                print("✓ [OK] Posse de HMAC confirmada: A chave fornecida é criptograficamente aceita pelo schema sosp_security.")
                return True
            else:
                print("✗ [FAIL] Falha de validação criptográfica: A chave fornecida difere do segredo ativo no PostgreSQL ou a assinatura foi rejeitada.")
                return False
    except Exception as e:
        print(f"✗ [ERROR] Erro durante a conexão ou validação de posse do HMAC: {type(e).__name__}")
        return False
    finally:
        # Remove referências de variáveis no escopo da função
        hmac_key = None
        signature = None
        payload = None
        if conn:
            try:
                conn.close()
            except Exception:
                pass


if __name__ == "__main__":
    success = verify_hmac_possession()
    sys.exit(0 if success else 1)
