#!/usr/bin/env python3
"""
SOSP — VALIDAÇÃO LOCAL DO RUNNER DO PORTÃO C.1
Executa o runner de C.1 contra um cluster PostgreSQL 18 local descartável via socket.
Comprova:
- Validação de identidade.
- BEGIN TRANSACTION READ ONLY.
- Verificação de transaction_read_only=on.
- Verificação das 38 tabelas e 2 views (security_invoker=true).
- Bloqueio de leitura de sosp_security.hmac_secret.
- Bloqueio de DDL/DML.
- Zero consumo de nonces.
"""

import sys
import os
import tempfile
import subprocess
import time
import shutil

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../.."))
BACKEND_DIR = os.path.join(WORKSPACE_ROOT, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from sosp_local_guard import assert_strictly_local_test_environment
assert_strictly_local_test_environment()

import psycopg
from run_gate_c1_readonly import run_gate_c1_readonly

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


def run_cmd(cmd):
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Comando falhou ({res.returncode}): {' '.join(cmd)}\n{res.stderr}")
    return res


def test_gate_c1_local():
    print("=" * 70)
    print("SOSP — HOMOLOGAÇÃO LOCAL DO SCRIPT DO PORTÃO C.1")
    print("=" * 70)

    temp_dir = tempfile.mkdtemp(prefix="pg_sosp_c1_test_")
    pg_data = os.path.join(temp_dir, "data")
    pg_socket = os.path.join(temp_dir, "socket")
    os.makedirs(pg_socket, exist_ok=True)
    pg_port = 55496

    admin_conn_str = f"host={pg_socket} port={pg_port} dbname=postgres user=postgres"

    proc = None
    try:
        run_cmd([f"{PG_BIN}/initdb", "-D", pg_data, "-U", "postgres", "--auth=trust", "--encoding=UTF8", "--locale=C"])
        with open(os.path.join(pg_data, "postgresql.conf"), "a") as f:
            f.write(f"\nunix_socket_directories = '{pg_socket}'\n")
            f.write(f"port = {pg_port}\n")
            f.write("listen_addresses = '127.0.0.1'\n")

        proc = subprocess.Popen([f"{PG_BIN}/postgres", "-D", pg_data], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.5)

        schema_path = os.path.join(WORKSPACE_ROOT, "docs/database/schema.sql")
        setup_4d2_path = os.path.join(CURRENT_DIR, "run_4d2_setup_security_context.sql")
        grants_4d2_path = os.path.join(CURRENT_DIR, "run_4d2_apply_minimum_grants.sql")
        rls_4d2_path = os.path.join(CURRENT_DIR, "run_4d2_apply_rls_policies.sql")

        run_cmd([f"{PG_BIN}/psql", admin_conn_str, "-f", schema_path])

        with psycopg.connect(admin_conn_str) as conn:
            with conn.cursor() as cur:
                # Cria tabelas do Django para completar as 38 tabelas físicas
                cur.execute("CREATE TABLE IF NOT EXISTS public.django_migrations (id serial primary key, app varchar(255), name varchar(255), applied timestamptz);")
                cur.execute("CREATE TABLE IF NOT EXISTS public.django_content_type (id serial primary key, app_label varchar(100), model varchar(100));")
                cur.execute("CREATE ROLE sosp_runtime_role NOLOGIN NOSUPERUSER NOBYPASSRLS;")
                cur.execute("CREATE ROLE sosp_runtime_app WITH LOGIN NOSUPERUSER NOBYPASSRLS INHERIT;")
                cur.execute("GRANT sosp_runtime_role TO sosp_runtime_app;")
                cur.execute("GRANT USAGE ON SCHEMA public TO sosp_runtime_role;")
            conn.commit()

        run_cmd([f"{PG_BIN}/psql", admin_conn_str, "-f", setup_4d2_path])
        run_cmd([f"{PG_BIN}/psql", admin_conn_str, "-f", grants_4d2_path])
        run_cmd([f"{PG_BIN}/psql", admin_conn_str, "-f", rls_4d2_path])

        # Define variáveis de ambiente para apontar para o cluster local
        os.environ["DB_HOST"] = pg_socket
        os.environ["DB_PORT"] = str(pg_port)
        os.environ["DB_NAME"] = "postgres"
        os.environ["DB_USER"] = "sosp_runtime_app"
        os.environ["DB_PASSWORD"] = "dummy"
        os.environ["DB_SSLMODE"] = "prefer"

        print("Cluster local e infraestrutura 4D.2 preparados. Invocando run_gate_c1_readonly()...\n")
        success = run_gate_c1_readonly()
        assert success is True, "run_gate_c1_readonly() falhou na execução local!"

        print("\n" + "=" * 70)
        print("✅ RUNNER DO PORTÃO C.1 VALIDADO COM SUCESSO LOCALMENTE!")
        print("=" * 70)
        return True

    finally:
        if proc:
            proc.terminate()
            proc.wait()
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    success = test_gate_c1_local()
    sys.exit(0 if success else 1)
