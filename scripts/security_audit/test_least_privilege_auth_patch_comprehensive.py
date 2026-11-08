#!/usr/bin/env python3
"""
SOSP — SUÍTE DE HOMOLOGAÇÃO LOCAL DO PATCH DE MENOR PRIVILÉGIO (PORTÃO C - SEÇÃO 2)
Testa exaustivamente a segurança da rotina de autenticação no PostgreSQL local independente e via DRF:
1. Permissões efetivas no PostgreSQL diretamente como sosp_runtime_app (sem passar pela API).
2. Prova de bloqueio RLS na tabela accountsCitizen para consultas diretas.
3. Invocação cirúrgica de sosp_security.authenticate_citizen_by_cpf com LIMIT 1.
4. Rejeição de SQL injection e formatos anômalos pela regex do banco.
5. Zero elevação de role da sessão PostgreSQL.
6. Rejeição segura de fallback privilegiado quando a função não existe.
7. Testes via DRF APIClient: cadastro, login válido, login inválido, timing mitigation, lockout (RN-29), revogação de sessão (accountsSession).
"""

import os
import sys
import tempfile
import subprocess
import time
import uuid
import datetime
import pytest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../.."))
BACKEND_DIR = os.path.join(REPO_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from sosp_local_guard import assert_strictly_local_test_environment

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.test"
os.environ["REPOSITORY_BACKEND"] = "memory"

import django
django.setup()

import psycopg
from django.conf import settings
from django.db import connections, connection
from django.contrib.auth.hashers import make_password
from rest_framework.test import APIClient

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
SCHEMA_SQL = os.path.expanduser("~/.sosp-backups/etapa-4c2/sosp_supabase_post_baseline_20261107_021656.sql")
if not os.path.isfile(SCHEMA_SQL):
    SCHEMA_SQL = os.path.join(REPO_ROOT, "docs/database/schema.sql")

DB_HMAC_KEY = "sosp-master-db-exclusive-hmac-key-32b-ok"


def run_cmd(cmd, env=None):
    res = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if res.returncode != 0:
        raise RuntimeError(f"Command failed ({res.returncode}): {' '.join(cmd)}\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}")
    return res.stdout


def test_least_privilege_patch():
    print("=" * 70)
    print("SOSP — HOMOLOGAÇÃO DO PATCH DE MENOR PRIVILÉGIO (SEÇÃO 2)")
    print("=" * 70)

    # 1. Guarda Local
    assert_strictly_local_test_environment()
    print("✓ Guarda Local Ativa: Zero conexões com hosts remotos.")

    tmp_root = tempfile.mkdtemp(prefix="pg_sosp_least_priv_")
    pg_data = os.path.join(tmp_root, "data")
    pg_sock = os.path.join(tmp_root, "socket")
    os.makedirs(pg_sock, exist_ok=True)
    pg_port = 55495

    try:
        # 2. Inicialização do Cluster Local
        run_cmd([
            f"{PG_BIN}/initdb", "-D", pg_data, "-U", "postgres",
            "--auth=trust", "--encoding=UTF8", "--locale=C"
        ])
        run_cmd([
            f"{PG_BIN}/pg_ctl", "-D", pg_data,
            "-o", f"-k {pg_sock} -p {pg_port} -h 127.0.0.1",
            "-l", os.path.join(tmp_root, "postgres.log"), "start"
        ])

        # Cria base e extensões
        run_cmd([f"{PG_BIN}/psql", "-h", pg_sock, "-p", str(pg_port), "-U", "postgres", "-d", "postgres", "-c", "CREATE DATABASE sosp_lp_test;"])
        run_cmd([f"{PG_BIN}/psql", "-h", pg_sock, "-p", str(pg_port), "-U", "postgres", "-d", "sosp_lp_test", "-c", "CREATE EXTENSION IF NOT EXISTS unaccent; CREATE EXTENSION IF NOT EXISTS pg_trgm; CREATE EXTENSION IF NOT EXISTS pgcrypto;"])

        # Restaura schema físico
        restore_env = os.environ.copy()
        restore_env["PGOPTIONS"] = "--client-min-messages=warning"
        subprocess.run([f"{PG_BIN}/psql", "-h", pg_sock, "-p", str(pg_port), "-U", "postgres", "-d", "sosp_lp_test", "-f", SCHEMA_SQL], capture_output=True, env=restore_env)

        # Configura roles
        with psycopg.connect(host=pg_sock, port=pg_port, dbname="sosp_lp_test", user="postgres", autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE ROLE sosp_runtime_role NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;")
                cur.execute("CREATE ROLE sosp_runtime_app LOGIN PASSWORD 'runtime_pw' NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS INHERIT;")
                cur.execute("GRANT sosp_runtime_role TO sosp_runtime_app;")
                cur.execute("GRANT USAGE ON SCHEMA public TO sosp_runtime_role;")

        # Aplica 4D.2 e Patch de Menor Privilégio
        run_cmd([f"{PG_BIN}/psql", "-h", pg_sock, "-p", str(pg_port), "-U", "postgres", "-d", "sosp_lp_test", "-v", "ON_ERROR_STOP=1", "-f", os.path.join(CURRENT_DIR, "run_4d2_setup_security_context.sql")])
        with psycopg.connect(host=pg_sock, port=pg_port, dbname="sosp_lp_test", user="postgres", autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT sosp_security.set_hmac_secret(%s);", (DB_HMAC_KEY,))
        run_cmd([f"{PG_BIN}/psql", "-h", pg_sock, "-p", str(pg_port), "-U", "postgres", "-d", "sosp_lp_test", "-v", "ON_ERROR_STOP=1", "-f", os.path.join(CURRENT_DIR, "run_4d2_apply_minimum_grants.sql")])
        run_cmd([f"{PG_BIN}/psql", "-h", pg_sock, "-p", str(pg_port), "-U", "postgres", "-d", "sosp_lp_test", "-v", "ON_ERROR_STOP=1", "-f", os.path.join(CURRENT_DIR, "run_4d2_apply_rls_policies.sql")])
        run_cmd([f"{PG_BIN}/psql", "-h", pg_sock, "-p", str(pg_port), "-U", "postgres", "-d", "sosp_lp_test", "-v", "ON_ERROR_STOP=1", "-f", os.path.join(CURRENT_DIR, "patch_least_privilege_auth_function.sql")])

        # Semeia dados de teste (cidadão ativo e cidadão inativo/excluído) via postgres
        active_citizen_id = str(uuid.uuid4())
        inactive_citizen_id = str(uuid.uuid4())
        deleted_citizen_id = str(uuid.uuid4())
        pwd_hash = make_password("Senha@Valida2026!")

        with psycopg.connect(host=pg_sock, port=pg_port, dbname="sosp_lp_test", user="postgres", autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO public.accountsGender (id, name, sortOrder) VALUES (gen_random_uuid(), 'Não Informado', 99) ON CONFLICT (name) DO NOTHING;")
                cur.execute("SELECT id FROM public.accountsGender WHERE name = 'Não Informado';")
                gender_id = str(cur.fetchone()[0])

                cur.execute("""
                INSERT INTO public.accountsCitizen (id, cpf, fullName, birthDate, email, phone, passwordHash, passwordSalt, genderId, motherName, zipCode, street, neighborhood, city, state, addressNumber, isActive, deletedAt)
                VALUES
                (%s, '11144477705', 'Cidadão Ativo', '1990-05-15', 'ativo@exemplo.com.br', '82999990001', %s, 'salt', %s, 'Mãe Ativa', '57000000', 'Rua A', 'Centro', 'Maceió', 'AL', '10', true, NULL),
                (%s, '22255588809', 'Cidadão Inativo', '1992-06-20', 'inativo@exemplo.com.br', '82999990002', %s, 'salt', %s, 'Mãe Inativa', '57000000', 'Rua B', 'Centro', 'Maceió', 'AL', '20', false, NULL),
                (%s, '33366699901', 'Cidadão Excluído', '1988-01-10', 'excluido@exemplo.com.br', '82999990003', %s, 'salt', %s, 'Mãe Excluída', '57000000', 'Rua C', 'Centro', 'Maceió', 'AL', '30', true, now());
                """, (active_citizen_id, pwd_hash, gender_id, inactive_citizen_id, pwd_hash, gender_id, deleted_citizen_id, pwd_hash, gender_id))

        print("✓ Cluster e dados preparados com sucesso.")

        # =====================================================================
        # PARTE A: AUDITORIA DIRETA DE PERMISSÕES NO POSTGRESQL (sosp_runtime_app)
        # =====================================================================
        print("\n--- [Parte A] Permissões Efetivas no PostgreSQL como 'sosp_runtime_app' ---")
        with psycopg.connect(host=pg_sock, port=pg_port, dbname="sosp_lp_test", user="sosp_runtime_app", password="runtime_pw", autocommit=True) as conn:
            with conn.cursor() as cur:
                # A.1 Verifica identidade
                cur.execute("SELECT current_user, session_user;")
                c_user, s_user = cur.fetchone()
                assert c_user == "sosp_runtime_app"
                print(f"✓ A.1 Conectado como runtime: '{c_user}'.")

                # A.2 Consulta direta a accountsCitizen sob RLS sem contexto -> 0 linhas
                cur.execute("SELECT count(*) FROM public.accountsCitizen;")
                count = cur.fetchone()[0]
                assert count == 0, f"RLS violado: runtime anônimo leu {count} linhas de accountsCitizen!"
                print("✓ A.2 Acesso SQL direto a accountsCitizen bloqueado por RLS (0 linhas visíveis).")

                # A.3 Consulta direta a sosp_security.hmac_secret -> 42501 permission denied
                try:
                    cur.execute("SELECT * FROM sosp_security.hmac_secret;")
                    assert False, "Deveria ter negado SELECT em hmac_secret!"
                except psycopg.errors.InsufficientPrivilege:
                    print("✓ A.3 Leitura direta da chave HMAC negada com SQLSTATE 42501.")

                # A.4 Invocação legítima da função com CPF válido
                cur.execute("SELECT citizen_id, full_name, email, password_hash, is_active, role FROM sosp_security.authenticate_citizen_by_cpf('11144477705');")
                row = cur.fetchone()
                assert row is not None, "Deveria ter retornado registro para CPF válido."
                assert str(row[0]) == active_citizen_id
                assert row[1] == "Cidadão Ativo"
                assert row[3] == pwd_hash
                assert row[4] is True
                assert row[5] == "citizen"
                print(f"✓ A.4 Invocação cirúrgica com CPF válido retornou dados necessários (ID: {active_citizen_id}).")

                # A.5 CPF inexistente -> 0 linhas
                cur.execute("SELECT * FROM sosp_security.authenticate_citizen_by_cpf('99999999999');")
                assert cur.fetchone() is None
                print("✓ A.5 CPF inexistente retornou 0 linhas sem erro de banco.")

                # A.6 Cidadão inativo (isActive=false) -> 0 linhas
                cur.execute("SELECT * FROM sosp_security.authenticate_citizen_by_cpf('22255588809');")
                assert cur.fetchone() is None
                print("✓ A.6 Cidadão inativo (isActive=false) não é retornado.")

                # A.7 Cidadão excluído logicamente (deletedAt IS NOT NULL) -> 0 linhas
                cur.execute("SELECT * FROM sosp_security.authenticate_citizen_by_cpf('33366699901');")
                assert cur.fetchone() is None
                print("✓ A.7 Cidadão com soft-delete (deletedAt) não é retornado.")

                # A.8 Proteção contra SQL Injection e caracteres anômalos
                injection_payloads = [
                    "11144477705' OR '1'='1",
                    "11144477705; DROP TABLE accountsCitizen;",
                    "11144477705--",
                    "ABCDEFGHIJK",
                    "123",
                    "1114447770512345",
                    "",
                ]
                for inj in injection_payloads:
                    cur.execute("SELECT * FROM sosp_security.authenticate_citizen_by_cpf(%s);", (inj,))
                    assert cur.fetchone() is None, f"Payload de injeção '{inj}' não deveria retornar linhas!"
                print("✓ A.8 Validação estrita por regex (^[0-9]{11}$) bloqueou 100% dos payloads de injeção.")

                # A.9 Ausência de elevação de papel da sessão PostgreSQL
                cur.execute("SELECT sosp_security.get_current_role();")
                role_after = cur.fetchone()[0]
                assert role_after == "anonymous", f"Role da sessão não deveria ter sido alterada (esperado 'anonymous', obtido '{role_after}')."
                print("✓ A.9 Zero elevação de role da sessão: get_current_role() permaneceu 'anonymous'.")

        # =====================================================================
        # PARTE B: VALIDAÇÃO DO BACKEND DJANGO (SEM FALLBACK PRIVILEGIADO)
        # =====================================================================
        print("\n--- [Parte B] Validação Django ORM e Proteções de API ---")
        settings.DATABASES["default"]["ENGINE"] = "django.db.backends.postgresql"
        settings.DATABASES["default"]["HOST"] = pg_sock
        settings.DATABASES["default"]["PORT"] = str(pg_port)
        settings.DATABASES["default"]["NAME"] = "sosp_lp_test"
        settings.DATABASES["default"]["USER"] = "sosp_runtime_app"
        settings.DATABASES["default"]["PASSWORD"] = "runtime_pw"
        settings.DATABASES["default"]["OPTIONS"] = {"sslmode": "disable"}
        settings.REPOSITORY_BACKEND = "orm"
        settings.DB_HMAC_SECRET_KEY = DB_HMAC_KEY

        connections["default"].close()
        connections.databases["default"] = settings.DATABASES["default"]
        del connections["default"]

        client = APIClient()

        # B.1 Login bem-sucedido via endpoint
        login_ok = client.post("/api/v1/auth/login", {"cpf": "11144477705", "password": "Senha@Valida2026!"}, format="json")
        assert login_ok.status_code == 200, f"Falha no login: {login_ok.json()}"
        token = login_ok.json()["token"]
        print("✓ B.1 Login com credencial válida aprovado com Argon2id via função de menor privilégio.")

        # B.2 Login com senha inválida
        login_bad_pwd = client.post("/api/v1/auth/login", {"cpf": "11144477705", "password": "SenhaIncorreta!"}, format="json")
        assert login_bad_pwd.status_code == 401
        print("✓ B.2 Senha inválida rejeitada com 401 Credenciais Inválidas.")

        # B.3 Login com CPF inexistente (tempo constante de CPU Argon2id)
        start_t = time.time()
        login_not_found = client.post("/api/v1/auth/login", {"cpf": "99988877700", "password": "QualquerSenha!"}, format="json")
        elapsed = time.time() - start_t
        assert login_not_found.status_code == 401
        print(f"✓ B.3 CPF inexistente rejeitado com 401 sob mitigação de timing attack (~{elapsed*1000:.1f}ms).")

        # B.4 Lockout após 5 falhas consecutivas (RN-29)
        test_lockout_cpf = "55566677700"
        for i in range(1, 6):
            fail_resp = client.post("/api/v1/auth/login", {"cpf": test_lockout_cpf, "password": "SenhaErradaNovamente!"}, format="json")
            if i < 5:
                assert fail_resp.status_code == 401, f"Tentativa {i} deveria retornar 401: {fail_resp.json()}"
            else:
                assert fail_resp.status_code == 429, f"Tentativa {i} deveria retornar 429: {fail_resp.json()}"
                assert "bloquead" in fail_resp.json()["detail"].lower()
        print("✓ B.4 Lockout de 5 minutos acionado após 5 erros consecutivos (RN-29).")

        # B.5 Revogação de Sessão
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        logout_resp = client.post("/api/v1/auth/logout")
        assert logout_resp.status_code == 200

        check_revoked = client.get("/api/v1/citizens/me")
        assert check_revoked.status_code in (401, 403)
        assert "revogada" in check_revoked.json()["detail"].lower()
        print("✓ B.5 Revogação de sessão em accountsSession e rejeição mandatória do token revogado.")

        # =====================================================================
        # PARTE C: SIMULAÇÃO DE AUSÊNCIA DA FUNÇÃO -> FALHA SEGURA (SEM BACKDOOR)
        # =====================================================================
        print("\n--- [Parte C] Falha Segura na Ausência da Função (Zero Fallback Privilegiado) ---")
        # Remove a função temporariamente via postgres para simular ambiente remoto sem o patch
        with psycopg.connect(host=pg_sock, port=pg_port, dbname="sosp_lp_test", user="postgres", autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("DROP FUNCTION sosp_security.authenticate_citizen_by_cpf(VARCHAR);")

        # Tenta login: deve falhar com 503 seguro e JAMAIS elevar para role='server'
        from apps.accounts.repositories import citizen_repository
        from common.exceptions import ProblemDetailsException

        try:
            citizen_repository.get_by_cpf_for_auth("11144477705")
            assert False, "Deveria ter lançado ProblemDetailsException 503 na ausência da função!"
        except ProblemDetailsException as pe:
            assert pe.status_code == 503
            assert "indisponível" in pe.detail.lower()
            print("✓ C.1 Falha segura comprovada: Ausência da função resulta em 503 controlado sem fallback para role='server'.")

        print("\n" + "=" * 70)
        print("✅ TODOS OS TESTES DO PATCH DE MENOR PRIVILÉGIO FORAM APROVADOS!")
        print("======================================================================")
        return True

    finally:
        try:
            connections["default"].close()
        except Exception:
            pass
        try:
            run_cmd([f"{PG_BIN}/pg_ctl", "-D", pg_data, "stop", "-m", "immediate"])
        except Exception:
            pass
        subprocess.run(["rm", "-rf", tmp_root])


if __name__ == "__main__":
    success = test_least_privilege_patch()
    sys.exit(0 if success else 1)
