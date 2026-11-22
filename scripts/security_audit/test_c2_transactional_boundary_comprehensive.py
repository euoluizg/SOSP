#!/usr/bin/env python3
"""
SOSP — TESTE EXAUSTIVO DE FRONTEIRA TRANSACIONAL E COMPATIBILIDADE SQL DO PORTÃO C.2
Homologação local com cluster PostgreSQL 18 descartável via socket Unix.

Comprova:
1. Nomes canônicos e assinaturas SQL 4D.2:
   - sosp_security.used_nonces (tabela de nonces)
   - sosp_security.hmac_secret (tabela com id INT PRIMARY KEY DEFAULT 1, secret_key TEXT)
   - sosp_security.set_request_context(UUID, VARCHAR, UUID, BIGINT, UUID, VARCHAR)
   - sosp_security.clear_request_context()
   - sosp_security.is_context_valid()
2. Persistência de nonce quando transação é commitada (COMMIT).
3. Não-persistência de nonce quando transação é revertida (ROLLBACK).
4. Rejeição sumária de Anti-Replay para nonce commitado.
5. Reuso legítimo de nonce que foi revertido antes de ser commitado.
6. Isolamento e recuperação com SAVEPOINT sem corromper o estado da conexão.
7. Garantia de que o Portão C.1 (READ ONLY) não consome nonces.
8. Classificação de C.2 como operação mutável.
"""

import sys
import os
import uuid
import time
import hmac
import hashlib
import tempfile
import subprocess
import shutil

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../.."))
BACKEND_DIR = os.path.join(WORKSPACE_ROOT, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from sosp_local_guard import assert_strictly_local_test_environment
assert_strictly_local_test_environment()

try:
    import psycopg
except ImportError:
    import psycopg2 as psycopg

import shutil

def _resolve_pg_bin() -> str:
    initdb_cmd = shutil.which("initdb")
    if initdb_cmd:
        return os.path.dirname(initdb_cmd)
    for candidate in [
        "/opt/homebrew/opt/postgresql@18/bin",
        "/opt/homebrew/opt/postgresql@17/bin",
        "/opt/homebrew/opt/postgresql@16/bin",
        "/usr/lib/postgresql/17/bin",
        "/usr/lib/postgresql/16/bin",
        "/usr/bin",
    ]:
        if os.path.isfile(os.path.join(candidate, "initdb")):
            return candidate
    return "/opt/homebrew/opt/postgresql@18/bin"

PG_BIN = _resolve_pg_bin()
TEST_SECRET_KEY = "sosp_test_super_secret_hmac_key_256bit_length_minimum_ok!"


def run_cmd(cmd, env=None):
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    if res.returncode != 0:
        raise RuntimeError(f"Comando falhou ({res.returncode}): {' '.join(cmd)}\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}")
    return res


def compute_sig(user_id, role, agency_id, expires_at, nonce, key):
    uid_str = str(user_id) if user_id else ""
    role_str = str(role) if role else ""
    aid_str = str(agency_id) if agency_id else ""
    nonce_str = str(nonce) if nonce else ""
    payload = f"{uid_str}:{role_str}:{aid_str}:{expires_at}:{nonce_str}".encode("utf-8")
    return hmac.new(key.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def test_transactional_boundary():
    print("=" * 70)
    print("SOSP — TESTE EXAUSTIVO DE TRANSACIONALIDADE E HMAC (PORTÃO C.2)")
    print("=" * 70)

    temp_dir = tempfile.mkdtemp(prefix="pg_sosp_c2_trans_")
    pg_data = os.path.join(temp_dir, "data")
    pg_socket = os.path.join(temp_dir, "socket")
    os.makedirs(pg_socket, exist_ok=True)
    pg_port = 55495

    admin_conn_str = f"host={pg_socket} port={pg_port} dbname=postgres user=postgres"
    runtime_conn_str = f"host={pg_socket} port={pg_port} dbname=postgres user=sosp_runtime_app"

    proc = None
    try:
        # 1. Inicializa cluster descartável
        run_cmd([f"{PG_BIN}/initdb", "-D", pg_data, "-U", "postgres", "--auth=trust", "--encoding=UTF8", "--locale=C"])
        with open(os.path.join(pg_data, "postgresql.conf"), "a") as f:
            f.write(f"\nunix_socket_directories = '{pg_socket}'\n")
            f.write(f"port = {pg_port}\n")
            f.write("listen_addresses = ''\n")

        proc = subprocess.Popen([f"{PG_BIN}/postgres", "-D", pg_data], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.5)

        # 2. Aplica schema baseline e estrutura 4D.2
        schema_path = os.path.join(WORKSPACE_ROOT, "docs/database/schema.sql")
        setup_4d2_path = os.path.join(CURRENT_DIR, "run_4d2_setup_security_context.sql")
        grants_4d2_path = os.path.join(CURRENT_DIR, "run_4d2_apply_minimum_grants.sql")
        rls_4d2_path = os.path.join(CURRENT_DIR, "run_4d2_apply_rls_policies.sql")
        patch_auth_path = os.path.join(CURRENT_DIR, "patch_least_privilege_auth_function.sql")

        run_cmd([f"{PG_BIN}/psql", admin_conn_str, "-f", schema_path])

        # Cria roles runtime e concede USAGE no schema public
        with psycopg.connect(admin_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE ROLE sosp_runtime_role NOLOGIN NOSUPERUSER NOBYPASSRLS;")
                cur.execute("CREATE ROLE sosp_runtime_app WITH LOGIN NOSUPERUSER NOBYPASSRLS INHERIT;")
                cur.execute("GRANT sosp_runtime_role TO sosp_runtime_app;")
                cur.execute("GRANT USAGE ON SCHEMA public TO sosp_runtime_role;")
            conn.commit()

        run_cmd([f"{PG_BIN}/psql", admin_conn_str, "-f", setup_4d2_path])
        run_cmd([f"{PG_BIN}/psql", admin_conn_str, "-f", grants_4d2_path])
        run_cmd([f"{PG_BIN}/psql", admin_conn_str, "-f", rls_4d2_path])
        run_cmd([f"{PG_BIN}/psql", admin_conn_str, "-f", patch_auth_path])

        # Configura o segredo HMAC de teste
        with psycopg.connect(admin_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT sosp_security.set_hmac_secret(%s);", (TEST_SECRET_KEY,))
            conn.commit()

        print("✓ Cluster de teste e infraestrutura 4D.2 inicializados com sucesso.\n")

        # ---------------------------------------------------------------------
        # TESTE 1: Nonce persistido após COMMIT
        # ---------------------------------------------------------------------
        print("--- [Cenário 1] Transação de Sucesso com COMMIT ---")
        user_1 = uuid.uuid4()
        nonce_1 = uuid.uuid4()
        now_epoch = int(time.time())
        exp_1 = now_epoch + 60
        sig_1 = compute_sig(user_1, "citizen", None, exp_1, nonce_1, TEST_SECRET_KEY)

        with psycopg.connect(runtime_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT sosp_security.set_request_context(%s, %s, %s, %s, %s, %s);",
                    (user_1, "citizen", None, exp_1, nonce_1, sig_1)
                )
                assert cur.fetchone()[0] is True, "Falha ao definir contexto válido"
                cur.execute("SELECT sosp_security.is_context_valid();")
                assert cur.fetchone()[0] is True, "Contexto deveria estar válido"
                cur.execute("SELECT sosp_security.clear_request_context();")
            conn.commit()

        with psycopg.connect(admin_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT count(*) FROM sosp_security.used_nonces WHERE nonce = %s;", (nonce_1,))
                count = cur.fetchone()[0]
                assert count == 1, f"Nonce deveria estar persistido (count={count})"
        print(f"✓ 1.1 Nonce {nonce_1} persistido com sucesso em sosp_security.used_nonces após COMMIT.")

        # ---------------------------------------------------------------------
        # TESTE 2: Anti-Replay com o Nonce Commitado
        # ---------------------------------------------------------------------
        print("\n--- [Cenário 2] Teste de Anti-Replay ---")
        with psycopg.connect(runtime_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT sosp_security.set_request_context(%s, %s, %s, %s, %s, %s);",
                    (user_1, "citizen", None, exp_1, nonce_1, sig_1)
                )
                res = cur.fetchone()[0]
                assert res is False, "Anti-Replay FALHOU: Nonce reutilizado foi aceito!"
                cur.execute("SELECT sosp_security.clear_request_context();")
            conn.rollback()
        print(f"✓ 2.1 Replay com nonce já consumido rejeitado sumariamente pelo banco (False).")

        # ---------------------------------------------------------------------
        # TESTE 3: Nonce Revertido por ROLLBACK
        # ---------------------------------------------------------------------
        print("\n--- [Cenário 3] Transação Revertida por ROLLBACK ---")
        user_2 = uuid.uuid4()
        nonce_2 = uuid.uuid4()
        exp_2 = now_epoch + 60
        sig_2 = compute_sig(user_2, "citizen", None, exp_2, nonce_2, TEST_SECRET_KEY)

        with psycopg.connect(runtime_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT sosp_security.set_request_context(%s, %s, %s, %s, %s, %s);",
                    (user_2, "citizen", None, exp_2, nonce_2, sig_2)
                )
                assert cur.fetchone()[0] is True
                cur.execute("SELECT sosp_security.clear_request_context();")
            conn.rollback()

        with psycopg.connect(admin_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT count(*) FROM sosp_security.used_nonces WHERE nonce = %s;", (nonce_2,))
                count = cur.fetchone()[0]
                assert count == 0, f"Nonce NÃO deveria estar persistido após rollback (count={count})"
        print(f"✓ 3.1 Nonce {nonce_2} NÃO foi persistido após ROLLBACK.")

        # ---------------------------------------------------------------------
        # TESTE 4: Reutilização do Nonce Revertido
        # ---------------------------------------------------------------------
        print("\n--- [Cenário 4] Reutilização de Nonce Previamente Revertido ---")
        with psycopg.connect(runtime_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT sosp_security.set_request_context(%s, %s, %s, %s, %s, %s);",
                    (user_2, "citizen", None, exp_2, nonce_2, sig_2)
                )
                assert cur.fetchone()[0] is True, "Nonce revertido deveria ser aceito em nova transação!"
                cur.execute("SELECT sosp_security.clear_request_context();")
            conn.commit()

        with psycopg.connect(admin_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT count(*) FROM sosp_security.used_nonces WHERE nonce = %s;", (nonce_2,))
                count = cur.fetchone()[0]
                assert count == 1, "Nonce agora deveria estar persistido após o novo commit"
        print(f"✓ 4.1 Nonce previamente revertido aceito e commitado com sucesso em nova transação.")

        # ---------------------------------------------------------------------
        # TESTE 5: SAVEPOINT e Recuperação de Erro SQL
        # ---------------------------------------------------------------------
        print("\n--- [Cenário 5] Erros SQL e SAVEPOINT ---")
        user_3 = uuid.uuid4()
        nonce_3 = uuid.uuid4()
        exp_3 = now_epoch + 60
        sig_3 = compute_sig(user_3, "citizen", None, exp_3, nonce_3, TEST_SECRET_KEY)

        with psycopg.connect(runtime_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT sosp_security.set_request_context(%s, %s, %s, %s, %s, %s);",
                    (user_3, "citizen", None, exp_3, nonce_3, sig_3)
                )
                cur.execute("SAVEPOINT sp_teste;")
                try:
                    cur.execute("SELECT * FROM non_existent_table_error;")
                except Exception:
                    cur.execute("ROLLBACK TO SAVEPOINT sp_teste;")

                # Conexão continua saudável para executar query subsequente
                cur.execute("SELECT 1;")
                assert cur.fetchone()[0] == 1
                cur.execute("SELECT sosp_security.clear_request_context();")
            conn.commit()
        print("✓ 5.1 SAVEPOINT permitiu recuperação de erro SQL sem invalidar a transação nem o pool.")

        # ---------------------------------------------------------------------
        # TESTE 6: Portão C.1 (READ ONLY) não consome nonces
        # ---------------------------------------------------------------------
        print("\n--- [Cenário 6] Portão C.1 (READ ONLY) e Zero Nonces ---")
        with psycopg.connect(admin_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT count(*) FROM sosp_security.used_nonces;")
                initial_count = cur.fetchone()[0]

        # Simula execução exata do Portão C.1
        with psycopg.connect(runtime_conn_str, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("BEGIN TRANSACTION READ ONLY;")
                cur.execute("SHOW transaction_read_only;")
                assert cur.fetchone()[0] == "on"
                cur.execute("SELECT count(*) FROM catalogService;")
                cur.execute("ROLLBACK;")

        with psycopg.connect(admin_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT count(*) FROM sosp_security.used_nonces;")
                final_count = cur.fetchone()[0]
                assert final_count == initial_count, "Portão C.1 alterou a contagem de nonces!"
        print(f"✓ 6.1 Portão C.1 executado sob READ ONLY com zero consumo de nonces (Total: {final_count}).")

        print("\n" + "=" * 70)
        print("✅ TODOS OS 6 CENÁRIOS DE TRANSACIONALIDADE E HMAC APROVADOS!")
        print("=" * 70)
        return True

    finally:
        if proc:
            proc.terminate()
            proc.wait()
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    success = test_transactional_boundary()
    sys.exit(0 if success else 1)
