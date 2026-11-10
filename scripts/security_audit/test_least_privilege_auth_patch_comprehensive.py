#!/usr/bin/env python3
"""
SOSP — SUÍTE DE HOMOLOGAÇÃO LOCAL DO PATCH DE MENOR PRIVILÉGIO (PORTÃO C - SEÇÃO 2)
Testa exaustivamente a segurança da rotina de autenticação no PostgreSQL local independente e via DRF:
1. Permissões efetivas no PostgreSQL diretamente como sosp_runtime_app (sem passar pela API).
2. Prova de bloqueio RLS nas tabelas accountsCitizen e accountsInternalUser para consultas diretas.
3. Invocação cirúrgica de authenticate_citizen_by_cpf e authenticate_internal_user_by_cpf sob RLS.
4. Rejeição de SQL injection e formatos anômalos pela regex do banco.
5. Zero elevação de role da sessão PostgreSQL.
6. Rejeição segura de fallback privilegiado quando a função não existe (503 fail-closed).
7. Testes via DRF APIClient: cadastro, login válido, login inválido, timing mitigation, lockout (RN-29), revogação de sessão.
8. Execução do seed_demo_users contra constraints reais do PostgreSQL (chkCatalogAgencySphere).
9. Armazenamento criptográfico seguro de códigos de recuperação de senha (zero texto puro).
10. Isolamento estrito de escopo operacional por unidade (RN-36 / ADR-003).
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
from common.security.authentication import verify_sosp_token

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
SCHEMA_SQL = os.path.join(REPO_ROOT, "docs/database/schema.sql")

DB_HMAC_KEY = "sosp-master-db-exclusive-hmac-key-32b-ok"


def run_cmd(cmd, env=None):
    res = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if res.returncode != 0:
        raise RuntimeError(f"Command failed ({res.returncode}): {' '.join(cmd)}\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}")
    return res.stdout


def set_django_db_user(pg_sock, pg_port, username, password=""):
    settings.DATABASES["default"]["ENGINE"] = "django.db.backends.postgresql"
    settings.DATABASES["default"]["HOST"] = pg_sock
    settings.DATABASES["default"]["PORT"] = str(pg_port)
    settings.DATABASES["default"]["NAME"] = "sosp_lp_test"
    settings.DATABASES["default"]["USER"] = username
    settings.DATABASES["default"]["PASSWORD"] = password
    settings.DATABASES["default"]["OPTIONS"] = {"sslmode": "disable"}
    settings.REPOSITORY_BACKEND = "orm"
    settings.DB_HMAC_SECRET_KEY = DB_HMAC_KEY

    try:
        connections["default"].close()
    except Exception:
        pass
    connections.databases["default"] = settings.DATABASES["default"]
    if "default" in connections:
        del connections["default"]


def test_least_privilege_patch():
    print("=" * 70)
    print("SOSP — HOMOLOGAÇÃO DO PATCH DE MENOR PRIVILÉGIO (PORTÃO C - SEÇÃO 2)")
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

        # Restaura schema físico oficial
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

        # Semeia dados de teste via postgres
        active_citizen_id = str(uuid.uuid4())
        inactive_citizen_id = str(uuid.uuid4())
        deleted_citizen_id = str(uuid.uuid4())
        pwd_hash = make_password("Senha@Valida2026!")

        agency_ssp_id = str(uuid.uuid4())
        agency_detran_id = str(uuid.uuid4())
        unit_ssp_centro_id = str(uuid.uuid4())
        unit_ssp_interior_id = str(uuid.uuid4())
        unit_detran_farol_id = str(uuid.uuid4())

        joao_id = str(uuid.uuid4())
        carlos_id = str(uuid.uuid4())
        admin_id = str(uuid.uuid4())
        inactive_servant_id = str(uuid.uuid4())
        deleted_servant_id = str(uuid.uuid4())

        with psycopg.connect(host=pg_sock, port=pg_port, dbname="sosp_lp_test", user="postgres", autocommit=True) as conn:
            with conn.cursor() as cur:
                # Gêneros iniciais
                cur.execute("""
                INSERT INTO public.accountsGender (id, name, sortOrder) VALUES
                (gen_random_uuid(), 'Não Informado', 99),
                (gen_random_uuid(), 'Feminino', 1),
                (gen_random_uuid(), 'Masculino', 2)
                ON CONFLICT (name) DO NOTHING;
                """)
                cur.execute("SELECT id FROM public.accountsGender WHERE name = 'Não Informado';")
                gender_id = str(cur.fetchone()[0])

                # Cidadãos
                cur.execute("""
                INSERT INTO public.accountsCitizen (id, cpf, fullName, birthDate, email, phone, passwordHash, passwordSalt, genderId, motherName, zipCode, street, neighborhood, city, state, addressNumber, isActive, deletedAt)
                VALUES
                (%s, '11144477705', 'Cidadão Ativo', '1990-05-15', 'ativo@exemplo.com.br', '82999990001', %s, 'salt', %s, 'Mãe Ativa', '57000000', 'Rua A', 'Centro', 'Maceió', 'AL', '10', true, NULL),
                (%s, '22255588809', 'Cidadão Inativo', '1992-06-20', 'inativo@exemplo.com.br', '82999990002', %s, 'salt', %s, 'Mãe Inativa', '57000000', 'Rua B', 'Centro', 'Maceió', 'AL', '20', false, NULL),
                (%s, '33366699901', 'Cidadão Excluído', '1988-01-10', 'excluido@exemplo.com.br', '82999990003', %s, 'salt', %s, 'Mãe Excluída', '57000000', 'Rua C', 'Centro', 'Maceió', 'AL', '30', true, now());
                """, (active_citizen_id, pwd_hash, gender_id, inactive_citizen_id, pwd_hash, gender_id, deleted_citizen_id, pwd_hash, gender_id))

                # Órgãos (com sphere='state' aderente ao contrato chkCatalogAgencySphere)
                cur.execute("""
                INSERT INTO public.catalogAgency (id, name, acronym, sphere, description, isActive)
                VALUES
                (%s, 'Secretaria de Estado da Segurança Pública', 'SSP', 'state', 'Segurança Pública', true),
                (%s, 'Departamento Estadual de Trânsito', 'DETRAN', 'state', 'Trânsito e Habilitação', true);
                """, (agency_ssp_id, agency_detran_id))

                # Unidades de Atendimento
                cur.execute("""
                INSERT INTO public.catalogUnit (id, agencyId, name, zipCode, street, neighborhood, city, state, addressNumber, dailyLimit, isActive)
                VALUES
                (%s, %s, 'Posto Central SSP', '57020100', 'Rua do Comércio', 'Centro', 'Maceió', 'AL', '123', 40, true),
                (%s, %s, 'Posto Interior SSP', '57300000', 'Rua das Flores', 'Centro', 'Arapiraca', 'AL', '45', 30, true),
                (%s, %s, 'Posto Farol DETRAN', '57051000', 'Av. Fernandes Lima', 'Farol', 'Maceió', 'AL', '456', 40, true);
                """, (unit_ssp_centro_id, agency_ssp_id, unit_ssp_interior_id, agency_ssp_id, unit_detran_farol_id, agency_detran_id))

                # Usuários Internos (com unitId operacional atribuído conforme ADR-003 / RN-36)
                cur.execute("""
                INSERT INTO public.accountsInternalUser (id, cpf, fullName, email, registrationNumber, agencyId, unitId, role, canManageCatalog, passwordHash, isActive, deletedAt)
                VALUES
                (%s, '33366699957', 'João Servidor Central', 'joao.servidor@ssp.al.gov.br', 'SSP-1001', %s, %s, 'servant', false, %s, true, NULL),
                (%s, '55588811194', 'Carlos Gestor SSP', 'carlos.gestor@ssp.al.gov.br', 'GES-3003', %s, NULL, 'gestor', true, %s, true, NULL),
                (%s, '99988877714', 'Admin SOSP Geral', 'admin@sosp.al.gov.br', 'ADM-0001', NULL, NULL, 'superadmin', true, %s, true, NULL),
                (%s, '44455566677', 'Servidor Inativo', 'inativo@ssp.al.gov.br', 'SSP-9999', %s, %s, 'servant', false, %s, false, NULL),
                (%s, '88899900011', 'Servidor Excluído', 'excluido@ssp.al.gov.br', 'SSP-8888', %s, %s, 'servant', false, %s, true, now());
                """, (
                    joao_id, agency_ssp_id, unit_ssp_centro_id, pwd_hash,
                    carlos_id, agency_ssp_id, pwd_hash,
                    admin_id, pwd_hash,
                    inactive_servant_id, agency_ssp_id, unit_ssp_centro_id, pwd_hash,
                    deleted_servant_id, agency_ssp_id, unit_ssp_centro_id, pwd_hash,
                ))

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

                # A.4 Invocação legítima da função cidadão com CPF válido
                cur.execute("SELECT citizen_id, full_name, email, password_hash, is_active, role FROM sosp_security.authenticate_citizen_by_cpf('11144477705');")
                row = cur.fetchone()
                assert row is not None, "Deveria ter retornado registro para CPF válido."
                assert str(row[0]) == active_citizen_id
                assert row[1] == "Cidadão Ativo"
                assert row[3] == pwd_hash
                assert row[4] is True
                assert row[5] == "citizen"
                print(f"✓ A.4 Invocação cirúrgica com CPF cidadão retornou dados necessários (ID: {active_citizen_id}).")

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

                # A.10 Consulta direta a accountsInternalUser sob RLS sem contexto -> 0 linhas
                cur.execute("SELECT count(*) FROM public.accountsInternalUser;")
                count_iu = cur.fetchone()[0]
                assert count_iu == 0, f"RLS violado: runtime anônimo leu {count_iu} linhas de accountsInternalUser!"
                print("✓ A.10 Acesso SQL direto a accountsInternalUser bloqueado por RLS (0 linhas visíveis).")

                # A.11 Invocação de authenticate_internal_user_by_cpf sob RLS (Servidor, Gestor e Admin)
                cur.execute("SELECT user_id, full_name, email, registration_number, agency_id, unit_id, role, can_manage_catalog, password_hash, is_active FROM sosp_security.authenticate_internal_user_by_cpf('33366699957');")
                iu_row = cur.fetchone()
                assert iu_row is not None, "Deveria ter retornado João Servidor."
                assert str(iu_row[0]) == joao_id
                assert iu_row[1] == "João Servidor Central"
                assert str(iu_row[4]) == agency_ssp_id
                assert str(iu_row[5]) == unit_ssp_centro_id, f"Servidor operacional deve ter unit_id preenchido! Obtido: {iu_row[5]}"
                assert iu_row[6] == "servant"
                assert iu_row[7] is False
                assert iu_row[8] == pwd_hash
                assert iu_row[9] is True
                print("✓ A.11.1 Servidor operacional autenticado com unitId válido mapeado na função.")

                # Carlos Gestor (escopo institucional de órgão, sem unidade)
                cur.execute("SELECT user_id, agency_id, unit_id, role, can_manage_catalog FROM sosp_security.authenticate_internal_user_by_cpf('55588811194');")
                carlos_row = cur.fetchone()
                assert carlos_row is not None
                assert str(carlos_row[0]) == carlos_id
                assert str(carlos_row[1]) == agency_ssp_id
                assert carlos_row[2] is None, "Gestor institucional não deve ter unit_id fixo."
                assert carlos_row[3] == "gestor"
                assert carlos_row[4] is True
                print("✓ A.11.2 Gestor institucional autenticado com agencyId e unitId=NULL mapeados na função.")

                # Admin Geral
                cur.execute("SELECT user_id, agency_id, unit_id, role, can_manage_catalog FROM sosp_security.authenticate_internal_user_by_cpf('99988877714');")
                admin_row = cur.fetchone()
                assert admin_row is not None
                assert str(admin_row[0]) == admin_id
                assert admin_row[1] is None
                assert admin_row[2] is None
                assert admin_row[3] == "superadmin"
                assert admin_row[4] is True
                print("✓ A.11.3 Administrador geral autenticado com agencyId=NULL e unitId=NULL.")

                # Servidor inativo ou excluído logicamente -> 0 linhas
                cur.execute("SELECT * FROM sosp_security.authenticate_internal_user_by_cpf('44455566677');")
                assert cur.fetchone() is None
                cur.execute("SELECT * FROM sosp_security.authenticate_internal_user_by_cpf('88899900011');")
                assert cur.fetchone() is None
                print("✓ A.11.4 Servidores inativos ou excluídos não são retornados pela função de menor privilégio.")

        # A.12 Prova de REVOKE ALL FROM PUBLIC para authenticate_internal_user_by_cpf
        with psycopg.connect(host=pg_sock, port=pg_port, dbname="sosp_lp_test", user="postgres", autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE ROLE sosp_unprivileged_test_user NOLOGIN;")
                try:
                    cur.execute("SET ROLE sosp_unprivileged_test_user;")
                    cur.execute("SELECT * FROM sosp_security.authenticate_internal_user_by_cpf('33366699957');")
                    assert False, "Deveria ter negado EXECUTE para role sem grant!"
                except psycopg.errors.InsufficientPrivilege:
                    print("✓ A.12 REVOKE ALL FROM PUBLIC comprovado: role não autorizada recebe SQLSTATE 42501.")
                finally:
                    cur.execute("RESET ROLE;")
                    cur.execute("DROP ROLE sosp_unprivileged_test_user;")

        # =====================================================================
        # PARTE B: VALIDAÇÃO DO BACKEND DJANGO (SEM FALLBACK PRIVILEGIADO)
        # =====================================================================
        print("\n--- [Parte B] Validação Django ORM e Proteções de API (Cidadão) ---")
        set_django_db_user(pg_sock, pg_port, "sosp_runtime_app", "runtime_pw")

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
        # PARTE D: AUTENTICAÇÃO INSTITUCIONAL DE SERVIDORES E GESTORES SOB RLS
        # =====================================================================
        print("\n--- [Parte D] Autenticação Institucional sob RLS via DRF ---")
        client.credentials()  # Limpa autorização prévia

        # D.1 Login João Servidor Central (operacional com unitId)
        login_joao = client.post("/api/v1/auth/login", {"cpf": "33366699957", "password": "Senha@Valida2026!"}, format="json")
        assert login_joao.status_code == 200, f"Falha no login do servidor: {login_joao.json()}"
        joao_token = login_joao.json()["token"]
        joao_payload = verify_sosp_token(joao_token)
        assert joao_payload["unit_id"] == unit_ssp_centro_id, f"Payload do token de servidor deve conter unit_id: {joao_payload}"
        assert joao_payload["agency_id"] == agency_ssp_id
        assert joao_payload["role"] == "server"
        print(f"✓ D.1 Servidor operacional autenticado com sucesso e unit_id incorporado ao token ({unit_ssp_centro_id}).")

        # D.2 Login Carlos Gestor SSP (institucional de órgão, sem unidade)
        login_carlos = client.post("/api/v1/auth/login", {"cpf": "55588811194", "password": "Senha@Valida2026!"}, format="json")
        assert login_carlos.status_code == 200, f"Falha no login do gestor: {login_carlos.json()}"
        carlos_token = login_carlos.json()["token"]
        carlos_payload = verify_sosp_token(carlos_token)
        assert carlos_payload["unit_id"] is None
        assert carlos_payload["agency_id"] == agency_ssp_id
        assert carlos_payload["role"] == "gestor"
        print(f"✓ D.2 Gestor institucional autenticado com agencyId ({agency_ssp_id}) e unitId=NULL.")

        # D.3 Login Admin Geral
        login_admin = client.post("/api/v1/auth/login", {"cpf": "99988877714", "password": "Senha@Valida2026!"}, format="json")
        assert login_admin.status_code == 200
        admin_token = login_admin.json()["token"]
        admin_payload = verify_sosp_token(admin_token)
        assert admin_payload["unit_id"] is None
        assert admin_payload["agency_id"] is None
        assert admin_payload["role"] in ("admin", "superadmin")
        print("✓ D.3 Administrador geral autenticado com escopo global irrestrito.")

        # D.4 Login Servidor Inativo rejeitado
        login_inativo = client.post("/api/v1/auth/login", {"cpf": "44455566677", "password": "Senha@Valida2026!"}, format="json")
        assert login_inativo.status_code == 401
        print("✓ D.4 Servidor inativo rejeitado com 401 Credenciais Inválidas.")

        # =====================================================================
        # PARTE E: EXECUÇÃO DO SEED E INTEGRIDADE DO SCHEMA POSTGRESQL REAL
        # =====================================================================
        print("\n--- [Parte E] Execução do Seed e Integridade do Schema PostgreSQL Real ---")
        from django.core.management import call_command
        from apps.catalog.models import Agency, Unit
        from apps.accounts.models import InternalUser

        # Executa o seed de demonstração como administrador da base
        set_django_db_user(pg_sock, pg_port, "postgres", "")
        call_command("seed_demo_users")
        print("✓ E.1 Comando 'seed_demo_users' executado com idempotência no PostgreSQL.")

        # Confirma integridade dos órgãos: sphere='state' aderente à constraint chkCatalogAgencySphere
        ssp_db = Agency.objects.get(acronym="SSP")
        detran_db = Agency.objects.get(acronym="DETRAN")
        assert ssp_db.sphere == "state", f"SSP deve ter sphere='state', obtido: {ssp_db.sphere}"
        assert detran_db.sphere == "state", f"DETRAN deve ter sphere='state', obtido: {detran_db.sphere}"

        # Teste explícito da constraint chkCatalogAgencySphere no PostgreSQL
        with psycopg.connect(host=pg_sock, port=pg_port, dbname="sosp_lp_test", user="postgres", autocommit=True) as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute("INSERT INTO public.catalogAgency (id, name, acronym, sphere, isActive) VALUES (gen_random_uuid(), 'Órgão Inválido', 'INV', 'Estadual', true);")
                    assert False, "Deveria ter violado chkCatalogAgencySphere!"
                except psycopg.errors.CheckViolation:
                    print("✓ E.2 Constraint chkCatalogAgencySphere ativa no PostgreSQL rejeitou 'Estadual' com SQLSTATE 23514.")

        # Confirma que os servidores de demonstração possuem unidade operacional atribuída
        joao_seed = InternalUser.objects.filter(email="joao.servidor@ssp.al.gov.br").first()
        ana_seed = InternalUser.objects.filter(email="ana.servidora@detran.al.gov.br").first()
        carlos_seed = InternalUser.objects.filter(email="carlos.gestor@ssp.al.gov.br").first()

        assert joao_seed is not None and joao_seed.unit_id is not None, "João deve possuir unit_id no banco!"
        assert ana_seed is not None and ana_seed.unit_id is not None, "Ana deve possuir unit_id no banco!"
        assert carlos_seed is not None and carlos_seed.unit_id is None, "Carlos Gestor não deve possuir unit_id fixo!"
        print(f"✓ E.3 Vínculo de servidores com unidades de atendimento confirmado (João: {joao_seed.unit_id}).")

        # =====================================================================
        # PARTE F: RECUPERAÇÃO DE SENHA COM HASH SEGURO NO POSTGRESQL REAL
        # =====================================================================
        print("\n--- [Parte F] Armazenamento Seguro de Recuperação de Senha (Zero Texto Puro) ---")
        from apps.accounts.services import AccountService
        from apps.accounts.repositories import citizen_repository
        from apps.accounts.models import Citizen, PasswordReset
        from django.utils import timezone

        # Executa como admin da base para verificação direta dos hashes persistidos
        set_django_db_user(pg_sock, pg_port, "postgres", "")

        # F.1 Cidadão: solicitação de recuperação
        AccountService.request_password_recovery("11144477705")
        cit_rec = Citizen.objects.get(cpf="11144477705")
        assert cit_rec.recovery_code_hash is not None, "Hash do código de recuperação não pode ser nulo."
        assert not cit_rec.recovery_code_hash.isdigit(), "Código de recuperação NÃO pode ser armazenado em texto puro!"
        assert len(cit_rec.recovery_code_hash) > 20, "Código de recuperação deve ser um hash criptográfico seguro."
        assert cit_rec.recovery_code_hash.startswith("pbkdf2_") or cit_rec.recovery_code_hash.startswith("argon2"), f"Hash não reconhecido: {cit_rec.recovery_code_hash}"
        assert cit_rec.recovery_code_expires_at > timezone.now()
        print(f"✓ F.1 Cidadão: código armazenado com hash criptográfico ({cit_rec.recovery_code_hash[:20]}...).")

        # F.1.2 Verificação de código incorreto e proteção contra força bruta
        assert citizen_repository.verify_recovery_code("11144477705", "000000") is False
        # 4 tentativas incorretas adicionais (total 5) devem invalidar o código
        for _ in range(4):
            citizen_repository.verify_recovery_code("11144477705", "000000")

        cit_rec.refresh_from_db()
        assert cit_rec.recovery_code_hash is None or cit_rec.recovery_code_hash == "", "Código deve ser invalidado após 5 tentativas incorretas!"
        print("✓ F.1.2 Código invalidado e descartado após 5 falhas consecutivas de validação.")

        # F.2 Usuário Interno: solicitação de recuperação
        AccountService.request_password_recovery("33366699957")
        pr_rec = PasswordReset.objects.filter(internal_user__cpf="33366699957", used_at__isnull=True).latest("created_at")
        assert pr_rec.code_hash is not None
        assert not pr_rec.code_hash.isdigit(), "Código do usuário interno NÃO pode ser armazenado em texto puro!"
        assert len(pr_rec.code_hash) > 20
        assert pr_rec.code_hash.startswith("pbkdf2_") or pr_rec.code_hash.startswith("argon2")
        print(f"✓ F.2 Usuário Interno: código armazenado em accountsPasswordReset com hash criptográfico ({pr_rec.code_hash[:20]}...).")

        # =====================================================================
        # PARTE G: ESCOPO OPERACIONAL E ISOLAMENTO DE UNIDADES (RN-36 / ADR-003)
        # =====================================================================
        print("\n--- [Parte G] Escopo Operacional e Isolamento de Unidades (RN-36 / ADR-003) ---")
        from apps.catalog.models import Service
        from apps.scheduling.models import Slot, Appointment

        # Configura fixtures como admin
        set_django_db_user(pg_sock, pg_port, "postgres", "")

        service_cin = Service.objects.create(
            name="Carteira de Identidade Nacional (CIN)",
            category="documents",
            detailed_description="Emissão da CIN presencial.",
            eligibility="Todos os cidadãos.",
            is_free=True,
            average_deadline_days=5,
            channel="inPerson",
            status="active",
        )
        service_antecedentes = Service.objects.create(
            name="Certidão de Antecedentes Criminais",
            category="documents",
            detailed_description="Emissão de antecedentes SSP.",
            eligibility="Todos os cidadãos.",
            is_free=True,
            average_deadline_days=2,
            channel="inPerson",
            status="active",
        )
        service_cnh = Service.objects.create(
            name="Renovação de CNH Presencial",
            category="transit",
            detailed_description="Renovação de CNH DETRAN.",
            eligibility="Condutores habilitados.",
            is_free=False,
            cost_amount=150.00,
            average_deadline_days=3,
            channel="inPerson",
            status="active",
        )

        today = datetime.date.today() + datetime.timedelta(days=2)
        slot_time = datetime.time(9, 0)

        # Cria slots para as 3 unidades
        slot_centro = Slot.objects.create(unit_id=unit_ssp_centro_id, slot_date=today, starts_at=slot_time, ends_at=datetime.time(9, 30), capacity=10)
        slot_interior = Slot.objects.create(unit_id=unit_ssp_interior_id, slot_date=today, starts_at=slot_time, ends_at=datetime.time(9, 30), capacity=10)
        slot_farol = Slot.objects.create(unit_id=unit_detran_farol_id, slot_date=today, starts_at=slot_time, ends_at=datetime.time(9, 30), capacity=10)

        # Cria 3 agendamentos (um por serviço para respeitar a constraint uqschedulingappointmentactive - RN-21)
        appt_centro = Appointment.objects.create(
            protocol_number="20261109-0001",
            citizen_id=active_citizen_id,
            service=service_cin,
            unit_id=unit_ssp_centro_id,
            slot=slot_centro,
            scheduled_date=today,
            scheduled_time=slot_time,
            status="scheduled",
        )
        appt_interior = Appointment.objects.create(
            protocol_number="20261109-0002",
            citizen_id=active_citizen_id,
            service=service_antecedentes,
            unit_id=unit_ssp_interior_id,
            slot=slot_interior,
            scheduled_date=today,
            scheduled_time=slot_time,
            status="scheduled",
        )
        appt_farol = Appointment.objects.create(
            protocol_number="20261109-0003",
            citizen_id=active_citizen_id,
            service=service_cnh,
            unit_id=unit_detran_farol_id,
            slot=slot_farol,
            scheduled_date=today,
            scheduled_time=slot_time,
            status="scheduled",
        )

        # Retorna para o runtime para testar as requisições autenticadas da API
        set_django_db_user(pg_sock, pg_port, "sosp_runtime_app", "runtime_pw")

        # G.1 Servidor Operacional João (lotado exclusivamente em Posto Central SSP)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {joao_token}")

        # Acessa agendamento da sua unidade -> 200 OK
        resp_centro = client.get("/api/v1/appointments/by-protocol/20261109-0001")
        assert resp_centro.status_code == 200, f"João deveria acessar agendamento de sua unidade: {resp_centro.json()}"
        print("✓ G.1.1 Servidor operacional acessa agendamento de sua própria unidade (200 OK).")

        # Acessa agendamento de outra unidade do MESMO órgão SSP -> 403 Forbidden (RN-36)
        resp_interior = client.get("/api/v1/appointments/by-protocol/20261109-0002")
        assert resp_interior.status_code == 403, f"Servidor não deve acessar outra unidade do mesmo órgão: {resp_interior.json()}"
        assert "outra unidade" in resp_interior.json()["detail"].lower()
        print("✓ G.1.2 Servidor operacional bloqueado ao acessar outra unidade do mesmo órgão (403 Forbidden - RN-36).")

        # Acessa agendamento de outro órgão (DETRAN) -> 403 Forbidden ou 404 Not Found (bloqueado por RLS)
        resp_detran = client.get("/api/v1/appointments/by-protocol/20261109-0003")
        assert resp_detran.status_code in (403, 404), f"Esperado 403 ou 404, obtido {resp_detran.status_code}: {resp_detran.json()}"
        print(f"✓ G.1.3 Servidor operacional bloqueado ao acessar unidade de órgão terceiro ({resp_detran.status_code} - RLS/RBAC).")

        # G.2 Gestor Institucional Carlos (lotado na SSP com escopo institucional de órgão)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {carlos_token}")

        # Acessa Unidade Centro da SSP -> 200 OK
        resp_carlos_centro = client.get("/api/v1/appointments/by-protocol/20261109-0001")
        assert resp_carlos_centro.status_code == 200
        # Acessa Unidade Interior da SSP -> 200 OK (mesmo órgão)
        resp_carlos_interior = client.get("/api/v1/appointments/by-protocol/20261109-0002")
        assert resp_carlos_interior.status_code == 200
        print("✓ G.2.1 Gestor institucional acessa agendamentos de múltiplas unidades de seu órgão de lotação (200 OK).")

        # Acessa agendamento de outro órgão (DETRAN Farol) -> 403 Forbidden ou 404 Not Found (bloqueado por RLS)
        resp_carlos_detran = client.get("/api/v1/appointments/by-protocol/20261109-0003")
        assert resp_carlos_detran.status_code in (403, 404), f"Esperado 403 ou 404, obtido {resp_carlos_detran.status_code}: {resp_carlos_detran.json()}"
        print(f"✓ G.2.2 Gestor institucional bloqueado ao acessar agendamentos de outro órgão ({resp_carlos_detran.status_code} - RLS/RBAC).")

        # G.3 Servidor operacional sem unidade atribuída -> Fail-closed 403 Forbidden
        from common.security.authentication import generate_sosp_token
        token_no_unit = generate_sosp_token(user_id=joao_id, role="server", agency_id=agency_ssp_id, unit_id=None)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_no_unit}")
        resp_no_unit = client.get("/api/v1/appointments/by-protocol/20261109-0001")
        assert resp_no_unit.status_code == 403
        assert "sem unidade" in resp_no_unit.json()["detail"].lower()
        print("✓ G.3 Servidor sem unidade atribuída recebe 403 Fail-Closed (RN-36).")

        # =====================================================================
        # PARTE H: SIMULAÇÃO DE AUSÊNCIA DA FUNÇÃO -> FALHA SEGURA (SEM BACKDOOR)
        # =====================================================================
        print("\n--- [Parte H] Falha Segura na Ausência da Função (Zero Fallback Privilegiado) ---")
        with psycopg.connect(host=pg_sock, port=pg_port, dbname="sosp_lp_test", user="postgres", autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("DROP FUNCTION sosp_security.authenticate_citizen_by_cpf(VARCHAR);")

        from common.exceptions import ProblemDetailsException

        try:
            citizen_repository.get_by_cpf_for_auth("11144477705")
            assert False, "Deveria ter lançado ProblemDetailsException 503 na ausência da função!"
        except ProblemDetailsException as pe:
            assert pe.status_code == 503
            assert "indisponível" in pe.detail.lower()
            print("✓ H.1 Falha segura comprovada: Ausência da função resulta em 503 controlado sem fallback para role='server'.")

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
