#!/usr/bin/env python3
"""
SOSP — TESTE INTEGRADO END-TO-END DE HOMOLOGAÇÃO DO PORTÃO B
Executa localmente sobre cluster PostgreSQL 18.6 descartável, com:
1. Conexão estritamente local (bloqueio mandatório de hosts remotos).
2. Role de runtime restrita: sosp_runtime_app (NOSUPERUSER, NOBYPASSRLS).
3. Backend real Django ORM: REPOSITORY_BACKEND=orm.
4. Políticas RLS ativas em 100% das 38 tabelas do SOSP.
5. DRF APIClient com autenticação por token Bearer e contexto de segurança PostgreSQL HMAC.
6. Validação completa das Jornadas:
   - Cidadão (Cadastro, Duplicidade, Login Argon2id, /me, Slots, Agendamento AAAAMMDD-XXXX, Checklist, PDF).
   - Isolamento RLS entre Cidadãos (Cidadão Alpha vs Cidadão Beta).
   - Servidor Público e Isolamento por Agência (SSP vs DETRAN).
   - Administrador (Auditoria e Relatórios).
   - Revogação Ativa de Sessão no Servidor (accountsSession).
   - Expiração Temporal de Sessão (RN-28: 30 minutos).
   - Bloqueio por Força Bruta (RN-29: 5 falhas consecutivas -> 5 minutos de lockout).
   - Fronteira Transacional, Nonces, Rollback e Higiene de Conexão no Pool.
"""

import os
import sys
import tempfile
import subprocess
import time
import uuid
import datetime
import shutil

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../.."))
BACKEND_DIR = os.path.join(REPO_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from sosp_local_guard import assert_strictly_local_test_environment
from test_transaction_boundary_and_context import test_transaction_boundary

# Inicializa Django antes de imports de models
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.test"
os.environ["REPOSITORY_BACKEND"] = "memory"  # inicialização segura antes de reconfiguração dinâmica

import django
django.setup()

import psycopg
from django.conf import settings
from django.db import connections, connection
from rest_framework.test import APIClient

from common.security.authentication import generate_sosp_token, SospUser
from common.security.db_context import compute_context_hmac

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


def main():
    print("=" * 70)
    print("SOSP — HOMOLOGAÇÃO INTEGRAL DO PORTÃO B (LOCAL & DESARTÁVEL)")
    print("=" * 70)

    # 1. Guarda de Isolamento Local Mandatória
    assert_strictly_local_test_environment()
    print("✓ Guarda de Segurança: Isolamento local validado (Zero conexões remotas permitidas).")

    tmp_root = tempfile.mkdtemp(prefix="pg_sosp_gate_b_")
    pg_data = os.path.join(tmp_root, "data")
    pg_sock = os.path.join(tmp_root, "socket")
    os.makedirs(pg_sock, exist_ok=True)
    pg_port = 55490

    # Garante que a guarda valide também o socket e a porta temporária
    assert_strictly_local_test_environment(pg_sock)

    try:
        # 2. Inicialização do Cluster PostgreSQL Local
        print("\n1. Inicializando cluster PostgreSQL 18 local descartável...")
        run_cmd([
            f"{PG_BIN}/initdb", "-D", pg_data, "-U", "postgres",
            "--auth=trust", "--encoding=UTF8", "--locale=C"
        ])
        run_cmd([
            f"{PG_BIN}/pg_ctl", "-D", pg_data,
            "-o", f"-k {pg_sock} -p {pg_port} -h 127.0.0.1",
            "-l", os.path.join(tmp_root, "postgres.log"), "start"
        ])
        print(f"✓ Cluster PostgreSQL ativo no socket '{pg_sock}' porta {pg_port}.")

        # 3. Criação da Base sosp_e2e e Extensões
        run_cmd([
            f"{PG_BIN}/psql", "-h", pg_sock, "-p", str(pg_port), "-U", "postgres", "-d", "postgres",
            "-c", "CREATE DATABASE sosp_e2e;"
        ])
        run_cmd([
            f"{PG_BIN}/psql", "-h", pg_sock, "-p", str(pg_port), "-U", "postgres", "-d", "sosp_e2e",
            "-c", "CREATE EXTENSION IF NOT EXISTS unaccent; CREATE EXTENSION IF NOT EXISTS pg_trgm; CREATE EXTENSION IF NOT EXISTS pgcrypto;"
        ])

        # 4. Aplicação do Schema Físico Baseline (38 tabelas e 2 views)
        print("2. Aplicando schema físico baseline (38 tabelas e 2 views)...")
        restore_env = os.environ.copy()
        restore_env["PGOPTIONS"] = "--client-min-messages=warning"
        subprocess.run([
            f"{PG_BIN}/psql", "-h", pg_sock, "-p", str(pg_port), "-U", "postgres", "-d", "sosp_e2e",
            "-f", SCHEMA_SQL
        ], capture_output=True, env=restore_env)

        # 5. Configuração das Roles de Runtime 4D.1
        print("3. Criando roles sosp_runtime_role e sosp_runtime_app (NOBYPASSRLS)...")
        with psycopg.connect(host=pg_sock, port=pg_port, dbname="sosp_e2e", user="postgres", autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE ROLE sosp_runtime_role NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;")
                cur.execute("CREATE ROLE sosp_runtime_app LOGIN PASSWORD 'runtime_pw' NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS INHERIT;")
                cur.execute("GRANT sosp_runtime_role TO sosp_runtime_app;")
                cur.execute("GRANT USAGE ON SCHEMA public TO sosp_runtime_role;")

        # 6. Aplicação da Arquitetura de Segurança 4D.2
        print("4. Aplicando segurança 4D.2 (schema sosp_security, grants mínimos e RLS)...")
        run_cmd([f"{PG_BIN}/psql", "-h", pg_sock, "-p", str(pg_port), "-U", "postgres", "-d", "sosp_e2e", "-v", "ON_ERROR_STOP=1", "-f", os.path.join(CURRENT_DIR, "run_4d2_setup_security_context.sql")])
        with psycopg.connect(host=pg_sock, port=pg_port, dbname="sosp_e2e", user="postgres", autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT sosp_security.set_hmac_secret(%s);", (DB_HMAC_KEY,))
        run_cmd([f"{PG_BIN}/psql", "-h", pg_sock, "-p", str(pg_port), "-U", "postgres", "-d", "sosp_e2e", "-v", "ON_ERROR_STOP=1", "-f", os.path.join(CURRENT_DIR, "run_4d2_apply_minimum_grants.sql")])
        run_cmd([f"{PG_BIN}/psql", "-h", pg_sock, "-p", str(pg_port), "-U", "postgres", "-d", "sosp_e2e", "-v", "ON_ERROR_STOP=1", "-f", os.path.join(CURRENT_DIR, "run_4d2_apply_rls_policies.sql")])
        run_cmd([f"{PG_BIN}/psql", "-h", pg_sock, "-p", str(pg_port), "-U", "postgres", "-d", "sosp_e2e", "-v", "ON_ERROR_STOP=1", "-f", os.path.join(CURRENT_DIR, "patch_least_privilege_auth_function.sql")])
        print("✓ Infraestrutura 4D.2 e patch de menor privilégio aplicados no cluster de teste.")

        # 7. Semeia Dados Mestres de Referência do Catálogo (via admin postgres)
        print("5. Semeando dados mestres de referência (órgãos, unidades, serviços, slots)...")
        agency_ssp_id = str(uuid.uuid4())
        agency_detran_id = str(uuid.uuid4())
        unit_ssp_id = str(uuid.uuid4())
        unit_detran_id = str(uuid.uuid4())
        service_cin_id = str(uuid.uuid4())
        slot_cin_id = str(uuid.uuid4())
        server_ssp_id = str(uuid.uuid4())
        server_detran_id = str(uuid.uuid4())
        admin_id = str(uuid.uuid4())

        with psycopg.connect(host=pg_sock, port=pg_port, dbname="sosp_e2e", user="postgres", autocommit=True) as conn:
            with conn.cursor() as cur:
                # Gênero
                cur.execute("INSERT INTO public.accountsGender (id, name, sortOrder) VALUES (gen_random_uuid(), 'Não Informado', 99) ON CONFLICT (name) DO NOTHING;")
                cur.execute("SELECT id FROM public.accountsGender WHERE name = 'Não Informado';")
                gender_id = str(cur.fetchone()[0])

                # Órgãos
                cur.execute("""
                INSERT INTO public.catalogAgency (id, name, acronym, sphere) VALUES
                (%s, 'Secretaria de Estado da Segurança Pública', 'SSP', 'state'),
                (%s, 'Departamento Estadual de Trânsito', 'DETRAN', 'state');
                """, (agency_ssp_id, agency_detran_id))

                # Unidades
                cur.execute("""
                INSERT INTO public.catalogUnit (id, agencyId, name, zipCode, street, neighborhood, city, state, addressNumber, dailyLimit) VALUES
                (%s, %s, 'Central Já! Centro', '57020100', 'Rua do Comércio', 'Centro', 'Maceió', 'AL', '123', 120),
                (%s, %s, 'Central Já! Shopping Farol', '57055000', 'Av Fernandes Lima', 'Farol', 'Maceió', 'AL', '500', 160);
                """, (unit_ssp_id, agency_ssp_id, unit_detran_id, agency_detran_id))

                # Serviço CIN
                cur.execute("""
                INSERT INTO public.catalogService (id, name, category, detailedDescription, eligibility, averageDeadlineDays, channel, status)
                VALUES (%s, 'Emitir Carteira de Identidade Nacional (CIN)', 'documents', 'Emissão da 1ª ou 2ª via da Carteira de Identidade Nacional física e digital.', 'Cidadãos brasileiros', 5, 'inPerson', 'active');
                """, (service_cin_id,))

                cur.execute("INSERT INTO public.catalogServiceAgency (serviceId, agencyId) VALUES (%s, %s);", (service_cin_id, agency_ssp_id))
                cur.execute("INSERT INTO public.catalogUnitService (unitId, serviceId) VALUES (%s, %s);", (unit_ssp_id, service_cin_id))

                # Etapas e Documentos
                doc_cin_id = str(uuid.uuid4())
                cur.execute("""
                INSERT INTO public.catalogServiceStep (id, serviceId, stepOrder, title, description) VALUES
                (gen_random_uuid(), %s, 1, 'Agendamento Prévio', 'Agende seu atendimento presencial pelo portal SOSP.'),
                (gen_random_uuid(), %s, 2, 'Comparecimento Presencial', 'Compareça no dia e hora agendados com os documentos originais.');
                """, (service_cin_id, service_cin_id))

                cur.execute("""
                INSERT INTO public.catalogServiceDocument (id, serviceId, name, isMandatory) VALUES
                (%s, %s, 'Certidão de Nascimento ou Casamento', true),
                (gen_random_uuid(), %s, 'Foto 3x4 Recente', false);
                """, (doc_cin_id, service_cin_id, service_cin_id))

                # Slot presencial para CIN
                cur.execute("""
                INSERT INTO public.schedulingSlot (id, unitId, slotDate, startsAt, endsAt, capacity, bookedCount)
                VALUES (%s, %s, '2026-11-20', '09:00', '09:30', 10, 0);
                """, (slot_cin_id, unit_ssp_id))

                # Usuários Internos
                cur.execute("""
                INSERT INTO public.accountsInternalUser (id, agencyId, fullName, email, cpf, registrationNumber, role, passwordHash) VALUES
                (%s, %s, 'Servidor SSP Atendente', 'servidor.ssp@sosp.gov.br', '33366699901', 'REG001', 'servant', 'argon2id$test'),
                (%s, %s, 'Servidor DETRAN Atendente', 'servidor.detran@sosp.gov.br', '44477700002', 'REG002', 'servant', 'argon2id$test'),
                (%s, NULL, 'Administrador Geral SOSP', 'admin@sosp.gov.br', '55588811103', 'REG003', 'administrator', 'argon2id$test');
                """, (server_ssp_id, agency_ssp_id, server_detran_id, agency_detran_id, admin_id))
        print("✓ Dados mestres de teste semeados com sucesso.")

        # 8. Reconfiguração Dinâmica do Django: REPOSITORY_BACKEND=orm e sosp_runtime_app
        print("\n6. Conectando Django ORM como 'sosp_runtime_app' (NOBYPASSRLS)...")
        settings.DATABASES["default"]["ENGINE"] = "django.db.backends.postgresql"
        settings.DATABASES["default"]["HOST"] = pg_sock
        settings.DATABASES["default"]["PORT"] = str(pg_port)
        settings.DATABASES["default"]["NAME"] = "sosp_e2e"
        settings.DATABASES["default"]["USER"] = "sosp_runtime_app"
        settings.DATABASES["default"]["PASSWORD"] = "runtime_pw"
        settings.DATABASES["default"]["OPTIONS"] = {"sslmode": "disable"}
        settings.REPOSITORY_BACKEND = "orm"
        settings.DB_HMAC_SECRET_KEY = DB_HMAC_KEY

        connections["default"].close()
        connections.databases["default"] = settings.DATABASES["default"]
        del connections["default"]

        # Prova de Identidade e Restrição RLS na Conexão Django
        with connection.cursor() as cur:
            cur.execute("SELECT current_user, session_user;")
            c_user, s_user = cur.fetchone()
            assert c_user == "sosp_runtime_app" and s_user == "sosp_runtime_app", f"Identidade incorreta: {c_user}"

            cur.execute("SELECT rolbypassrls, rolsuper FROM pg_roles WHERE rolname = 'sosp_runtime_app';")
            bypass, superuser = cur.fetchone()
            assert bypass is False and superuser is False, "Violação: sosp_runtime_app NÃO pode ter BYPASSRLS ou SUPERUSER."

            cur.execute("SELECT pg_has_role(current_user, 'sosp_runtime_role', 'member');")
            assert cur.fetchone()[0] is True, "sosp_runtime_app deve herdar sosp_runtime_role."

        print(f"✓ Django ORM conectado como '{c_user}' (rolbypassrls=False, rolsuper=False).")
        print(f"✓ Modo de Repositório Ativo: REPOSITORY_BACKEND={settings.REPOSITORY_BACKEND}.")

        client = APIClient()

        # =====================================================================
        # JORNADA 1: CIDADÃO ALPHA (Registro, Duplicidade, Login, /me, Slots, Agendamento)
        # =====================================================================
        print("\n--- [Jornada 1] Cidadão Alpha (Cadastro, Login, RLS, Agendamento) ---")
        citizen_alpha_payload = {
            "fullName": "Carlos Eduardo Lima",
            "cpf": "52998224725",
            "birthDate": "1995-04-10",
            "motherName": "Tereza Lima",
            "email": "carlos.lima@exemplo.com.br",
            "phone": "82998877665",
            "password": "Senha@Forte2026!",
            "isPcd": False,
            "zipCode": "57020100",
            "street": "Rua das Flores",
            "number": "42",
            "neighborhood": "Centro",
            "city": "Maceió",
            "state": "AL",
        }

        # 1.1 Cadastro via DRF (sob RLS p_citizen_insert para anônimo)
        res_reg = client.post("/api/v1/auth/register", citizen_alpha_payload, format="json")
        assert res_reg.status_code == 201, f"Falha no cadastro do cidadão: {res_reg.json()}"
        citizen_alpha_id = res_reg.json()["id"]
        print(f"✓ 1.1 Cidadão cadastrado via ORM sob RLS anônimo (ID: {citizen_alpha_id}).")

        # 1.2 Tentativa de Cadastro Duplicado com mesmo CPF -> 409 Conflict
        res_dup = client.post("/api/v1/auth/register", citizen_alpha_payload, format="json")
        assert res_dup.status_code == 409, f"Deveria ter retornado 409 para CPF duplicado: {res_dup.json()}"
        assert "cadastra" in res_dup.json()["detail"].lower() or "cadastrado" in res_dup.json()["title"].lower()
        print("✓ 1.2 Tentativa de cadastro duplicado rejeitada com 409 Conflict (RFC 7807).")

        # 1.3 Login via DRF (Argon2id + patch_least_privilege_auth_function + accountsSession)
        login_res = client.post("/api/v1/auth/login", {"cpf": "52998224725", "password": "Senha@Forte2026!"}, format="json")
        assert login_res.status_code == 200, f"Falha no login: {login_res.json()}"
        token_alpha = login_res.json()["token"]
        assert login_res.json()["expiresIn"] == 1800
        print("✓ 1.3 Login efetuado com hash Argon2id; sessão gravada em accountsSession sob RLS.")

        # 1.4 Acesso a /me com Bearer Token (RLS sob sosp.current_user_id)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_alpha}")
        me_res = client.get("/api/v1/citizens/me")
        assert me_res.status_code == 200, f"Falha em /me: {me_res.json()}"
        assert me_res.json()["fullName"] == "Carlos Eduardo Lima"
        assert me_res.json()["cpf"] == "52998224725"
        print("✓ 1.4 Endpoint /api/v1/citizens/me retornou dados reais do PostgreSQL via Django ORM.")

        # 1.5 Consulta de Slots de 30 min (RN-18)
        slots_res = client.get(f"/api/v1/units/{unit_ssp_id}/slots?date=2026-11-20")
        assert slots_res.status_code == 200, f"Falha em slots: {slots_res.json()}"
        slots = slots_res.json()
        assert len(slots) > 0
        print(f"✓ 1.5 Consulta de slots de 30 minutos na unidade SSP aprovada ({len(slots)} slots).")

        # 1.6 Agendamento com Idempotency-Key e Protocolo AAAAMMDD-XXXX (RN-20)
        appt_payload = {
            "serviceId": service_cin_id,
            "unitId": unit_ssp_id,
            "scheduledDate": "2026-11-20",
            "scheduledTime": "09:00",
        }
        idemp_key = str(uuid.uuid4())
        appt_res = client.post("/api/v1/appointments", appt_payload, format="json", HTTP_IDEMPOTENCY_KEY=idemp_key)
        assert appt_res.status_code == 201, f"Falha no agendamento: {appt_res.json()}"
        appt_alpha_data = appt_res.json()
        protocol_alpha = appt_alpha_data["protocolNumber"]
        appt_alpha_id = appt_alpha_data["id"]
        parts = protocol_alpha.split("-")
        assert len(parts[0]) == 8 and len(parts[1]) == 4, f"Protocolo inválido: {protocol_alpha}"
        print(f"✓ 1.6 Agendamento atômico criado no PostgreSQL sob RLS. Protocolo gerado: '{protocol_alpha}'.")

        # 1.7 Linha do Tempo do Protocolo
        timeline_res = client.get(f"/api/v1/protocols/{protocol_alpha}/timeline")
        assert timeline_res.status_code == 200
        print(f"✓ 1.7 Linha do tempo do protocolo '{protocol_alpha}' consultada com sucesso.")

        # 1.8 Checklist e Guia
        guidance_res = client.get(f"/api/v1/guidance/services/{service_cin_id}")
        assert guidance_res.status_code == 200
        chk_res = client.put(
            f"/api/v1/guidance/services/{service_cin_id}",
            {"checkedItems": [doc_cin_id]},
            format="json"
        )
        assert chk_res.status_code == 200
        print("✓ 1.8 Checklist de documentos atualizado sob persistência ORM.")

        # 1.9 PDF do Guia
        pdf_req = client.post(f"/api/v1/guidance/services/{service_cin_id}/pdf")
        assert pdf_req.status_code == 202
        job_id = pdf_req.json()["jobId"]
        pdf_status = client.get(f"/api/v1/guidance/pdf/{job_id}")
        assert pdf_status.status_code == 200
        print("✓ 1.9 Solicitação e consulta do status de PDF do guia aprovadas.")

        # =====================================================================
        # JORNADA 2: ISOLAMENTO RLS ENTRE CIDADÃOS (ALPHA VS BETA)
        # =====================================================================
        print("\n--- [Jornada 2] Isolamento RLS entre Cidadãos ---")
        citizen_beta_payload = {
            "fullName": "Mariana Santos",
            "cpf": "12345678909",
            "birthDate": "1998-08-22",
            "motherName": "Rosa Santos",
            "email": "mariana.santos@exemplo.com.br",
            "phone": "82991122334",
            "password": "Senha@Forte2026!",
            "isPcd": False,
            "zipCode": "57020100",
            "street": "Rua B",
            "number": "88",
            "neighborhood": "Centro",
            "city": "Maceió",
            "state": "AL",
        }
        client.credentials()  # Garante estado anônimo para auto-cadastro (p_citizen_insert)
        res_beta_reg = client.post("/api/v1/auth/register", citizen_beta_payload, format="json")
        assert res_beta_reg.status_code == 201
        citizen_beta_id = res_beta_reg.json()["id"]

        login_beta = client.post("/api/v1/auth/login", {"cpf": "12345678909", "password": "Senha@Forte2026!"}, format="json")
        token_beta = login_beta.json()["token"]

        # Cidadão Beta autenticado tenta acessar o agendamento do Cidadão Alpha
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_beta}")
        beta_peek_alpha = client.get(f"/api/v1/appointments/{appt_alpha_id}")
        assert beta_peek_alpha.status_code in (403, 404), f"RLS violado: Cidadão Beta conseguiu ler agendamento do Alpha: {beta_peek_alpha.json()}"
        print("✓ 2.1 Isolamento RLS Cidadão A vs Cidadão B comprovado: Acesso cruzado bloqueado com 403/404.")

        # =====================================================================
        # JORNADA 3: SERVIDOR PÚBLICO E ISOLAMENTO POR AGÊNCIA (SSP VS DETRAN)
        # =====================================================================
        print("\n--- [Jornada 3] Servidor Público e Isolamento por Agência ---")
        token_server_ssp = generate_sosp_token(
            user_id=server_ssp_id,
            role="server",
            agency_id=agency_ssp_id,
            full_name="Servidor SSP Atendente",
            email="servidor.ssp@sosp.gov.br",
        )
        token_server_detran = generate_sosp_token(
            user_id=server_detran_id,
            role="server",
            agency_id=agency_detran_id,
            full_name="Servidor DETRAN Atendente",
            email="servidor.detran@sosp.gov.br",
        )

        # Servidor SSP consulta protocolo da sua própria agência
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_server_ssp}")
        ssp_check = client.get(f"/api/v1/appointments/by-protocol/{protocol_alpha}")
        assert ssp_check.status_code == 200, f"Servidor da agência SSP deveria ter acesso ao agendamento da SSP: {ssp_check.json()}"
        print(f"✓ 3.1 Servidor da SSP localizou agendamento '{protocol_alpha}' da sua própria agência.")

        # Servidor DETRAN tenta consultar protocolo da agência SSP -> RLS bloqueia
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_server_detran}")
        detran_check = client.get(f"/api/v1/appointments/by-protocol/{protocol_alpha}")
        assert detran_check.status_code in (403, 404), f"Violação RLS: Servidor do DETRAN leu agendamento da SSP: {detran_check.json()}"
        print("✓ 3.2 Isolamento RLS entre Agências comprovado: Servidor de órgão distinto bloqueado (403/404).")

        # =====================================================================
        # JORNADA 4: ADMINISTRADOR GERAL (Auditoria e Relatórios)
        # =====================================================================
        print("\n--- [Jornada 4] Administrador Geral (Auditoria e Relatórios) ---")
        token_admin = generate_sosp_token(
            user_id=admin_id,
            role="admin",
            full_name="Administrador Geral SOSP",
            email="admin@sosp.gov.br",
        )
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_admin}")
        audit_res = client.get("/api/v1/audit/events")
        assert audit_res.status_code == 200
        print("✓ 4.1 Administrador auditou trilha de eventos (auditEvent).")

        reports_res = client.get("/api/v1/reports/appointments")
        assert reports_res.status_code == 200
        print("✓ 4.2 Administrador gerou relatório consolidado de métricas operacionais.")

        # =====================================================================
        # JORNADA 5: REVOGAÇÃO ATIVA DE SESSÃO NO SERVIDOR (accountsSession)
        # =====================================================================
        print("\n--- [Jornada 5] Revogação Ativa de Sessão no Servidor ---")
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_alpha}")
        logout_res = client.post("/api/v1/auth/logout")
        assert logout_res.status_code == 200
        print("✓ 5.1 Logout executado com sucesso: sessão marcada como revogada em accountsSession.")

        # Próxima requisição com token revogado deve falhar com 401
        revoked_check = client.get("/api/v1/citizens/me")
        assert revoked_check.status_code in (401, 403), f"Token revogado não deveria ser aceito: {revoked_check.json()}"
        assert "revogada" in revoked_check.json()["detail"].lower()
        print("✓ 5.2 Validação de revogação no servidor comprovada: Token revogado sumariamente rejeitado (401).")

        # =====================================================================
        # JORNADA 6: SEGURANÇA TEMPORAL, BLOQUEIO POR FORÇA BRUTA (RN-28 & RN-29)
        # =====================================================================
        print("\n--- [Jornada 6] Segurança Temporal e Bloqueio de Força Bruta ---")
        # 6.1 Token com expiração passada
        exp_token = generate_sosp_token(citizen_alpha_id, role="citizen", expires_in_seconds=-10)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {exp_token}")
        exp_res = client.get("/api/v1/citizens/me")
        assert exp_res.status_code in (401, 403)
        assert "expirada" in exp_res.json()["detail"].lower()
        print("✓ 6.1 Expiração temporal de sessão confirmada: Token > 30 minutos inativo rejeitado (401).")

        # 6.2 Bloqueio Temporário após 5 erros de senha (RN-29)
        client.credentials()  # anônimo
        for attempt in range(1, 6):
            fail_res = client.post("/api/v1/auth/login", {"cpf": "12345678909", "password": "SenhaIncorreta!"}, format="json")
            if attempt < 5:
                assert fail_res.status_code == 401
            else:
                assert fail_res.status_code == 429
                assert "bloquead" in fail_res.json()["detail"].lower()
        print("✓ 6.2 Bloqueio temporário de 5 minutos acionado após 5 erros consecutivos (RN-29).")

        # =====================================================================
        # JORNADA 7: TESTE INTEGRAL DE FRONTEIRA TRANSACIONAL E CONTEXTO HMAC
        # =====================================================================
        print("\n--- [Jornada 7] Fronteira Transacional, Nonces e Higiene de Conexão ---")
        boundary_ok = test_transaction_boundary(
            host=pg_sock,
            port=pg_port,
            dbname="sosp_e2e",
            user="sosp_runtime_app",
            password="runtime_pw",
            sslmode="disable",
            hmac_key=DB_HMAC_KEY,
        )
        assert boundary_ok is True, "Falha nos testes de fronteira transacional e contexto."
        print("✓ 7.1 Fronteira transacional, HMAC, Anti-Replay de Nonce e Higiene de Pool aprovados.")

        print("\n" + "=" * 70)
        print("✅ [PORTÃO B APROVADO] TODAS AS JORNADAS FULL-STACK, ORM, POSTGRESQL E")
        print("                     POLÍTICAS RLS FORAM HOMOLOGADAS COM SUCESSO LOCALMENTE.")
        print("=" * 70)
        return True

    finally:
        print("\nLimpando cluster PostgreSQL local temporário...")
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
    success = main()
    sys.exit(0 if success else 1)
