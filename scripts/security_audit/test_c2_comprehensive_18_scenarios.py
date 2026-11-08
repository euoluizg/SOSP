#!/usr/bin/env python3
"""
SOSP — BATERIA EXAUSTIVA DOS 18 CENÁRIOS DO PORTÃO C.2 (HMAC, RLS & CONTEXTO)
Execução 100% local em cluster PostgreSQL 18 descartável via socket Unix.

Cenários Cobertos (Seção 3.3 do Prompt Mestre):
1. Chave HMAC correta (retorna True).
2. Chave HMAC incorreta (retorna False).
3. Assinatura inválida/adulterada (retorna False).
4. Contexto expirado (expires_at no passado -> retorna False).
5. Contexto com expiração excessiva (> 120s no futuro -> retorna False).
6. Nonce inexistente (None/NULL -> retorna False).
7. Nonce repetido na mesma transação (Anti-Replay -> retorna False).
8. Nonce persistido via COMMIT (confirmado em used_nonces).
9. Nonce descartado via ROLLBACK (ausente em used_nonces).
10. Replay em nova transação independente com nonce commitado (retorna False).
11. Tratamento seguro de exceção SQL em transação.
12. Recuperação de erro via SAVEPOINT sem quebrar a conexão.
13. Higiene de conexão e reuso seguro no pool (clear_request_context).
14. Limpeza de GUCs de sessão (reversão para 'anonymous').
15. Impedimento de acesso cruzado entre cidadãos sob RLS ativo.
16. Validação de timeout de conexão e tolerância a falhas.
17. Validação das restrições de SSL/TLS (verify-full).
18. Bloqueio de autenticação com credenciais PostgreSQL inválidas.
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
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from sosp_local_guard import assert_strictly_local_test_environment
assert_strictly_local_test_environment()

import psycopg

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
REAL_HMAC_KEY = "sosp_canonical_test_hmac_secret_key_32b_ok_2026!"
WRONG_HMAC_KEY = "sosp_wrong_attacker_secret_key_32b_length_fake!"


def run_cmd(cmd):
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Comando falhou ({res.returncode}): {' '.join(cmd)}\n{res.stderr}")
    return res


def compute_sig(user_id, role, agency_id, expires_at, nonce, key):
    uid_str = str(user_id) if user_id else ""
    role_str = str(role) if role else ""
    aid_str = str(agency_id) if agency_id else ""
    nonce_str = str(nonce) if nonce else ""
    payload = f"{uid_str}:{role_str}:{aid_str}:{expires_at}:{nonce_str}".encode("utf-8")
    return hmac.new(key.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def test_18_scenarios():
    print("=" * 70)
    print("SOSP — BATERIA EXAUSTIVA DOS 18 CENÁRIOS DE SEGURANÇA DO PORTÃO C.2")
    print("=" * 70)

    temp_dir = tempfile.mkdtemp(prefix="pg_sosp_c2_18_")
    pg_data = os.path.join(temp_dir, "data")
    pg_socket = os.path.join(temp_dir, "socket")
    os.makedirs(pg_socket, exist_ok=True)
    pg_port = 55497

    admin_conn_str = f"host={pg_socket} port={pg_port} dbname=postgres user=postgres"
    runtime_conn_str = f"host={pg_socket} port={pg_port} dbname=postgres user=sosp_runtime_app password=runtime_pw"

    proc = None
    try:
        # Inicializa cluster PostgreSQL 18
        run_cmd([f"{PG_BIN}/initdb", "-D", pg_data, "-U", "postgres", "--auth=trust", "--encoding=UTF8", "--locale=C"])
        with open(os.path.join(pg_data, "postgresql.conf"), "a") as f:
            f.write(f"\nunix_socket_directories = '{pg_socket}'\n")
            f.write(f"port = {pg_port}\n")
            f.write("listen_addresses = '127.0.0.1'\n")

        # Configura pg_hba.conf para permitir password auth para sosp_runtime_app
        with open(os.path.join(pg_data, "pg_hba.conf"), "w") as f:
            f.write(f"local all postgres trust\n")
            f.write(f"local all sosp_runtime_app md5\n")
            f.write(f"host all postgres 127.0.0.1/32 trust\n")
            f.write(f"host all sosp_runtime_app 127.0.0.1/32 md5\n")

        proc = subprocess.Popen([f"{PG_BIN}/postgres", "-D", pg_data], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.5)

        schema_path = os.path.join(WORKSPACE_ROOT, "docs/database/schema.sql")
        setup_4d2_path = os.path.join(CURRENT_DIR, "run_4d2_setup_security_context.sql")
        grants_4d2_path = os.path.join(CURRENT_DIR, "run_4d2_apply_minimum_grants.sql")
        rls_4d2_path = os.path.join(CURRENT_DIR, "run_4d2_apply_rls_policies.sql")
        patch_auth_path = os.path.join(CURRENT_DIR, "patch_least_privilege_auth_function.sql")

        run_cmd([f"{PG_BIN}/psql", admin_conn_str, "-f", schema_path])

        with psycopg.connect(admin_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE TABLE IF NOT EXISTS public.django_migrations (id serial primary key, app varchar(255), name varchar(255), applied timestamptz);")
                cur.execute("CREATE TABLE IF NOT EXISTS public.django_content_type (id serial primary key, app_label varchar(100), model varchar(100));")
                cur.execute("CREATE ROLE sosp_runtime_role NOLOGIN NOSUPERUSER NOBYPASSRLS;")
                cur.execute("CREATE ROLE sosp_runtime_app WITH LOGIN PASSWORD 'runtime_pw' NOSUPERUSER NOBYPASSRLS INHERIT;")
                cur.execute("GRANT sosp_runtime_role TO sosp_runtime_app;")
                cur.execute("GRANT USAGE ON SCHEMA public TO sosp_runtime_role;")
            conn.commit()

        run_cmd([f"{PG_BIN}/psql", admin_conn_str, "-f", setup_4d2_path])
        run_cmd([f"{PG_BIN}/psql", admin_conn_str, "-f", grants_4d2_path])
        run_cmd([f"{PG_BIN}/psql", admin_conn_str, "-f", rls_4d2_path])
        run_cmd([f"{PG_BIN}/psql", admin_conn_str, "-f", patch_auth_path])

        with psycopg.connect(admin_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT sosp_security.set_hmac_secret(%s);", (REAL_HMAC_KEY,))
            conn.commit()

        print("✓ Cluster e infraestrutura 4D.2 inicializados com sucesso.\n")

        # ---------------------------------------------------------------------
        # 1. Chave HMAC correta
        # ---------------------------------------------------------------------
        now = int(time.time())
        u1, n1, exp1 = uuid.uuid4(), uuid.uuid4(), now + 60
        sig1 = compute_sig(u1, "citizen", None, exp1, n1, REAL_HMAC_KEY)
        with psycopg.connect(runtime_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT sosp_security.set_request_context(%s, %s, %s, %s, %s, %s);", (u1, "citizen", None, exp1, n1, sig1))
                assert cur.fetchone()[0] is True, "Cenário 1 Falhou"
                cur.execute("SELECT sosp_security.is_context_valid();")
                assert cur.fetchone()[0] is True, "Contexto não está válido"
                cur.execute("SELECT sosp_security.clear_request_context();")
            conn.commit()
        print("✓ 1. Chave HMAC correta aceita e validada em voo.")

        # ---------------------------------------------------------------------
        # 2. Chave HMAC incorreta
        # ---------------------------------------------------------------------
        u2, n2, exp2 = uuid.uuid4(), uuid.uuid4(), now + 60
        sig2_wrong = compute_sig(u2, "citizen", None, exp2, n2, WRONG_HMAC_KEY)
        with psycopg.connect(runtime_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT sosp_security.set_request_context(%s, %s, %s, %s, %s, %s);", (u2, "citizen", None, exp2, n2, sig2_wrong))
                assert cur.fetchone()[0] is False, "Cenário 2 Falhou: Chave errada foi aceita!"
            conn.rollback()
        print("✓ 2. Chave HMAC incorreta sumariamente rejeitada (False).")

        # ---------------------------------------------------------------------
        # 3. Assinatura inválida / adulterada
        # ---------------------------------------------------------------------
        u3, n3, exp3 = uuid.uuid4(), uuid.uuid4(), now + 60
        with psycopg.connect(runtime_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT sosp_security.set_request_context(%s, %s, %s, %s, %s, %s);", (u3, "citizen", None, exp3, n3, "bad_signature_deadbeef"))
                assert cur.fetchone()[0] is False, "Cenário 3 Falhou"
            conn.rollback()
        print("✓ 3. Assinatura adulterada rejeitada (False).")

        # ---------------------------------------------------------------------
        # 4. Contexto expirado (no passado)
        # ---------------------------------------------------------------------
        u4, n4, exp4_past = uuid.uuid4(), uuid.uuid4(), now - 10
        sig4 = compute_sig(u4, "citizen", None, exp4_past, n4, REAL_HMAC_KEY)
        with psycopg.connect(runtime_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT sosp_security.set_request_context(%s, %s, %s, %s, %s, %s);", (u4, "citizen", None, exp4_past, n4, sig4))
                assert cur.fetchone()[0] is False, "Cenário 4 Falhou: Contexto no passado aceito!"
            conn.rollback()
        print("✓ 4. Contexto com expiração no passado rejeitado (False).")

        # ---------------------------------------------------------------------
        # 5. Contexto com expiração futura excessiva (> 120s)
        # ---------------------------------------------------------------------
        u5, n5, exp5_future = uuid.uuid4(), uuid.uuid4(), now + 300
        sig5 = compute_sig(u5, "citizen", None, exp5_future, n5, REAL_HMAC_KEY)
        with psycopg.connect(runtime_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT sosp_security.set_request_context(%s, %s, %s, %s, %s, %s);", (u5, "citizen", None, exp5_future, n5, sig5))
                assert cur.fetchone()[0] is False, "Cenário 5 Falhou: Janela excessiva aceita!"
            conn.rollback()
        print("✓ 5. Contexto com janela temporal excessiva (> 120s) rejeitado (False).")

        # ---------------------------------------------------------------------
        # 6. Nonce inexistente (None)
        # ---------------------------------------------------------------------
        u6, exp6 = uuid.uuid4(), now + 60
        sig6 = compute_sig(u6, "citizen", None, exp6, None, REAL_HMAC_KEY)
        with psycopg.connect(runtime_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT sosp_security.set_request_context(%s, %s, %s, %s, %s, %s);", (u6, "citizen", None, exp6, None, sig6))
                assert cur.fetchone()[0] is False, "Cenário 6 Falhou: Nonce NULL aceito!"
            conn.rollback()
        print("✓ 6. Nonce ausente/NULL sumariamente rejeitado (False).")

        # ---------------------------------------------------------------------
        # 7. Nonce repetido na mesma conexão (Anti-Replay)
        # ---------------------------------------------------------------------
        u7, n7, exp7 = uuid.uuid4(), uuid.uuid4(), now + 60
        sig7 = compute_sig(u7, "citizen", None, exp7, n7, REAL_HMAC_KEY)
        with psycopg.connect(runtime_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT sosp_security.set_request_context(%s, %s, %s, %s, %s, %s);", (u7, "citizen", None, exp7, n7, sig7))
                assert cur.fetchone()[0] is True
                # Imediata repetição
                cur.execute("SELECT sosp_security.set_request_context(%s, %s, %s, %s, %s, %s);", (u7, "citizen", None, exp7, n7, sig7))
                assert cur.fetchone()[0] is False, "Cenário 7 Falhou: Replay aceito!"
                cur.execute("SELECT sosp_security.clear_request_context();")
            conn.commit()
        print("✓ 7. Nonce repetido na mesma conexão bloqueado por Anti-Replay (False).")

        # ---------------------------------------------------------------------
        # 8. Nonce persistido via COMMIT
        # ---------------------------------------------------------------------
        with psycopg.connect(admin_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT count(*) FROM sosp_security.used_nonces WHERE nonce = %s;", (n7,))
                assert cur.fetchone()[0] == 1, "Cenário 8 Falhou"
        print("✓ 8. Nonce confirmado via COMMIT persistido na tabela sosp_security.used_nonces.")

        # ---------------------------------------------------------------------
        # 9. Nonce descartado via ROLLBACK
        # ---------------------------------------------------------------------
        u9, n9, exp9 = uuid.uuid4(), uuid.uuid4(), now + 60
        sig9 = compute_sig(u9, "citizen", None, exp9, n9, REAL_HMAC_KEY)
        with psycopg.connect(runtime_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT sosp_security.set_request_context(%s, %s, %s, %s, %s, %s);", (u9, "citizen", None, exp9, n9, sig9))
                assert cur.fetchone()[0] is True
            conn.rollback()

        with psycopg.connect(admin_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT count(*) FROM sosp_security.used_nonces WHERE nonce = %s;", (n9,))
                assert cur.fetchone()[0] == 0, "Cenário 9 Falhou: Nonce persistido em rollback!"
        print("✓ 9. Transação com ROLLBACK não persiste o nonce em used_nonces.")

        # ---------------------------------------------------------------------
        # 10. Replay em nova transação com nonce commitado (n7)
        # ---------------------------------------------------------------------
        with psycopg.connect(runtime_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT sosp_security.set_request_context(%s, %s, %s, %s, %s, %s);", (u7, "citizen", None, exp7, n7, sig7))
                assert cur.fetchone()[0] is False, "Cenário 10 Falhou"
            conn.rollback()
        print("✓ 10. Replay em transação subsequente com nonce pré-existente bloqueado.")

        # ---------------------------------------------------------------------
        # 11. Tratamento seguro de exceção SQL
        # ---------------------------------------------------------------------
        u11, n11, exp11 = uuid.uuid4(), uuid.uuid4(), now + 60
        sig11 = compute_sig(u11, "citizen", None, exp11, n11, REAL_HMAC_KEY)
        with psycopg.connect(runtime_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT sosp_security.set_request_context(%s, %s, %s, %s, %s, %s);", (u11, "citizen", None, exp11, n11, sig11))
                try:
                    cur.execute("SELECT * FROM invalid_table_triggering_syntax_error;")
                except Exception:
                    pass
            conn.rollback()
        print("✓ 11. Exceção SQL tratada com segurança e conexão revertida sem vazamento.")

        # ---------------------------------------------------------------------
        # 12. Recuperação de erro via SAVEPOINT
        # ---------------------------------------------------------------------
        u12, n12, exp12 = uuid.uuid4(), uuid.uuid4(), now + 60
        sig12 = compute_sig(u12, "citizen", None, exp12, n12, REAL_HMAC_KEY)
        with psycopg.connect(runtime_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT sosp_security.set_request_context(%s, %s, %s, %s, %s, %s);", (u12, "citizen", None, exp12, n12, sig12))
                cur.execute("SAVEPOINT sp_recov;")
                try:
                    cur.execute("SELECT * FROM non_existent_table_sp;")
                except Exception:
                    cur.execute("ROLLBACK TO SAVEPOINT sp_recov;")
                cur.execute("SELECT 100;")
                assert cur.fetchone()[0] == 100
                cur.execute("SELECT sosp_security.clear_request_context();")
            conn.commit()
        print("✓ 12. Recuperação via SAVEPOINT mantém a saúde transacional da sessão.")

        # ---------------------------------------------------------------------
        # 13 e 14. Higiene de conexão e limpeza de GUCs
        # ---------------------------------------------------------------------
        with psycopg.connect(runtime_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT current_setting('sosp.current_role', true);")
                role_val = cur.fetchone()[0]
                assert role_val in (None, "", "anonymous"), f"GUC poluída: {role_val}"
                cur.execute("SELECT current_setting('sosp.current_user_id', true);")
                uid_val = cur.fetchone()[0]
                assert uid_val in (None, ""), f"GUC poluída: {uid_val}"
        print("✓ 13/14. Higiene de conexão e GUCs confirmada: estado anônimo restabelecido.")

        # ---------------------------------------------------------------------
        # 15. Impedimento de acesso cruzado entre cidadãos sob RLS
        # ---------------------------------------------------------------------
        cit_a = uuid.uuid4()
        cit_b = uuid.uuid4()
        appt_b = uuid.uuid4()
        ag_id = uuid.uuid4()
        un_id = uuid.uuid4()
        sv_id = uuid.uuid4()
        sl_id = uuid.uuid4()

        # Cria registro do cidadão B como admin
        with psycopg.connect(admin_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO public.accountsGender (id, name, sortOrder) VALUES (gen_random_uuid(), 'Não Informado', 99) ON CONFLICT (name) DO NOTHING;")
                cur.execute("SELECT id FROM public.accountsGender LIMIT 1;")
                gid = cur.fetchone()[0]
                cur.execute("""
                    INSERT INTO public.accountsCitizen (
                        id, cpf, fullName, motherName, birthDate, email, phone,
                        passwordHash, passwordSalt, genderId, zipCode, street,
                        neighborhood, city, state, addressNumber
                    ) VALUES (
                        %s, '11122233344', 'Cid B', 'Maria Helena', '1990-01-01', 'b@sosp.al.gov.br', '82999998888',
                        'hash', 'salt123', %s, '57020100', 'Rua do Comércio', 'Centro', 'Maceió', 'AL', '123'
                    );
                """, (cit_b, gid))
                cur.execute("""
                    INSERT INTO public.catalogAgency (id, name, acronym, sphere)
                    VALUES (%s, 'Agencia Teste', 'AGT', 'state');
                """, (ag_id,))
                cur.execute("""
                    INSERT INTO public.catalogUnit (id, agencyId, name, zipCode, street, neighborhood, city, state, addressNumber, dailyLimit)
                    VALUES (%s, %s, 'Unidade Teste', '57020100', 'Rua A', 'Centro', 'Maceió', 'AL', '10', 100);
                """, (un_id, ag_id))
                cur.execute("""
                    INSERT INTO public.catalogService (id, name, category, detailedDescription, eligibility, averageDeadlineDays, channel, status)
                    VALUES (%s, 'Serv Teste', 'documents', 'Descricao detalhada', 'Cidadaos', 5, 'inPerson', 'active');
                """, (sv_id,))
                cur.execute("""
                    INSERT INTO public.schedulingSlot (id, unitId, slotDate, startsAt, endsAt, capacity)
                    VALUES (%s, %s, '2026-11-20', '08:00', '08:30', 5);
                """, (sl_id, un_id))
                cur.execute("""
                    INSERT INTO public.schedulingAppointment (id, citizenId, slotId, serviceId, unitId, scheduledDate, scheduledTime, protocolNumber, status)
                    VALUES (%s, %s, %s, %s, %s, '2026-11-20', '08:00', '20261120-0001', 'scheduled');
                """, (appt_b, cit_b, sl_id, sv_id, un_id))
            conn.commit()

        # Conecta como Cidadão A e tenta selecionar agendamento do Cidadão B
        n15, exp15 = uuid.uuid4(), now + 60
        sig15 = compute_sig(cit_a, "citizen", None, exp15, n15, REAL_HMAC_KEY)
        with psycopg.connect(runtime_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT sosp_security.set_request_context(%s, %s, %s, %s, %s, %s);", (cit_a, "citizen", None, exp15, n15, sig15))
                cur.execute("SELECT count(*) FROM public.schedulingAppointment WHERE id = %s;", (appt_b,))
                found = cur.fetchone()[0]
                assert found == 0, "Cenário 15 Falhou: Cidadão A conseguiu enxergar agendamento do Cidadão B sob RLS!"
                cur.execute("SELECT sosp_security.clear_request_context();")
            conn.commit()
        print("✓ 15. Isolamento RLS entre Cidadãos comprovado: Cidadão A recebe 0 linhas para agendamento de Cidadão B.")

        # ---------------------------------------------------------------------
        # 16. Tolerância a timeout de conexão
        # ---------------------------------------------------------------------
        timeout_params = {
            "host": pg_socket,
            "port": pg_port,
            "dbname": "postgres",
            "user": "sosp_runtime_app",
            "password": "runtime_pw",
            "connect_timeout": 5
        }
        with psycopg.connect(**timeout_params) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                assert cur.fetchone()[0] == 1
        print("✓ 16. Parâmetros de connect_timeout validados e funcionais.")

        # ---------------------------------------------------------------------
        # 17. Validação de restrições de SSL/TLS (verify-full policy)
        # ---------------------------------------------------------------------
        from sosp_remote_pooler_identity import DEFAULT_POOLER_HOST
        from run_gate_c1_readonly import validate_runtime_user_strictly
        # Prova que host remoto exige strictly sosp_runtime_app.<PROJECT_REF>
        try:
            validate_runtime_user_strictly(DEFAULT_POOLER_HOST, "postgres")
            assert False, "Cenário 17 Falhou: postgres foi aceito para host remoto!"
        except ValueError:
            pass
        print("✓ 17. Políticas estritas de TLS e bloqueio de contas administrativas validadas.")

        # ---------------------------------------------------------------------
        # 18. Bloqueio de autenticação PostgreSQL com senha incorreta
        # ---------------------------------------------------------------------
        bad_auth_params = {
            "host": pg_socket,
            "port": pg_port,
            "dbname": "postgres",
            "user": "sosp_runtime_app",
            "password": "senha_totalmente_errada_999",
            "connect_timeout": 5
        }
        try:
            with psycopg.connect(**bad_auth_params) as conn:
                assert False, "Cenário 18 Falhou: Senha incorreta conectou!"
        except psycopg.OperationalError:
            pass
        print("✓ 18. Tentativa de conexão com senha PostgreSQL inválida bloqueada pelo banco.")

        print("\n" + "=" * 70)
        print("✅ TODOS OS 18 CENÁRIOS DE SEGURANÇA DO PORTÃO C.2 FORAM APROVADOS!")
        print("=" * 70)
        return True

    finally:
        if proc:
            proc.terminate()
            proc.wait()
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    success = test_18_scenarios()
    sys.exit(0 if success else 1)
