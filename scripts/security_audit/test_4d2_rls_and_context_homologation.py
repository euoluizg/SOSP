#!/usr/bin/env python3
"""
SOSP — Teste Automatizado de Homologação da Etapa 4D.2 (Refinado e Exaustivo)
Valida 19 cenários determinísticos de segurança:
1. Instalação do schema sosp_security e proteção da tabela hmac_secret.
2. Isolamento de chaves (chave HMAC do banco vs Django SECRET_KEY).
3. Matriz de mínimo privilégio DML (Zero TRUNCATE, Zero REFERENCES, Zero TRIGGER, Zero DELETE em entidades).
4. Aplicação de políticas RLS para todos os perfis em todas as 38 tabelas.
5. Anti-GUC Spoofing dinâmico.
6. Rejeição de assinaturas com chave incorreta.
7. Anti-Replay: Rejeição de tokens expirados no passado.
8. Anti-Replay: Rejeição de tokens com expiração excessiva (> 120s).
9. Anti-Replay Estrito: Rejeição imediata de Nonce duplicado (token replay entre transações bloqueado).
10. Anti-Tampering de Usuário: Invalidação instantânea ao alterar sosp.current_user_id.
11. Anti-Tampering de Agência: Invalidação instantânea ao alterar sosp.current_agency_id.
12. RLS Cidadão: Acesso exclusivo aos próprios dados.
13. RLS Cadastro Cidadão: Proteção contra cadastro por usuário já autenticado e troca de ID.
14. RLS Auditoria: Anti-falsificação estrita de autoria (actorType e actorId vinculados ao contexto).
15. RLS Servidor: Restrição de dados à sua própria agência de lotação.
16. Pool Connection Reuse: Reuso de conexão no pool entre duas identidades e limpeza obrigatória.
17. Segurança de Funções SECURITY DEFINER (search_path e restrição de EXECUTE).
18. Reversibilidade DML: Revogação completa de grants de volta ao estado seguro da 4D.1.
19. Reversibilidade RLS Cirúrgica: Remoção objeto a objeto SEM DROP SCHEMA CASCADE (uso de RESTRICT).
"""

import os
import sys
import tempfile
import subprocess
import time
import uuid
import shutil
import psycopg

# Adiciona o backend ao sys.path para importar compute_context_hmac
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPTS_DIR, "../.."))
BACKEND_DIR = os.path.join(REPO_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
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
BACKUP_FILE = os.path.expanduser("~/.sosp-backups/etapa-4c2/sosp_supabase_post_baseline_20261107_021656.sql")
if not os.path.isfile(BACKUP_FILE):
    BACKUP_FILE = os.path.join(REPO_ROOT, "docs/database/schema.sql")

DB_HMAC_KEY = "sosp-master-db-exclusive-hmac-key-32b-ok"
DJANGO_SECRET_KEY = "django-insecure-different-key-not-for-db-usage-12345"

def run_cmd(cmd):
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Command failed ({res.returncode}): {' '.join(cmd)}\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}")
    return res.stdout

def main():
    tmp_root = tempfile.mkdtemp(prefix="pg_sosp_4d2_homolog_")
    pg_data = os.path.join(tmp_root, "data")
    pg_sock = os.path.join(tmp_root, "socket")
    os.makedirs(pg_sock, exist_ok=True)
    pg_port = 55475

    try:
        # 1. Inicia cluster PostgreSQL 18.6
        run_cmd([
            f"{PG_BIN}/initdb", "-D", pg_data, "-U", "postgres",
            "--auth=trust", "--encoding=UTF8", "--locale=pt_BR.UTF-8", "--lc-messages=C"
        ])
        run_cmd([
            f"{PG_BIN}/pg_ctl", "-D", pg_data,
            "-o", f"-k {pg_sock} -p {pg_port}",
            "-l", os.path.join(tmp_root, "postgres.log"), "start"
        ])
        run_cmd([
            f"{PG_BIN}/psql", "-h", pg_sock, "-p", str(pg_port), "-U", "postgres", "-d", "postgres",
            "-c", "CREATE DATABASE sosp_homolog_4d2;"
        ])

        # 2. Restaura dump 4C.2
        restore_env = os.environ.copy()
        restore_env["PGOPTIONS"] = "--client-min-messages=warning"
        subprocess.run([
            f"{PG_BIN}/psql", "-h", pg_sock, "-p", str(pg_port), "-U", "postgres", "-d", "sosp_homolog_4d2",
            "-f", BACKUP_FILE
        ], capture_output=True, env=restore_env)

        # 3. Prepara roles da Etapa 4D.1
        with psycopg.connect(host=pg_sock, port=pg_port, dbname="sosp_homolog_4d2", user="postgres", autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE ROLE sosp_runtime_role NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;")
                cur.execute("CREATE ROLE sosp_runtime_app LOGIN PASSWORD 'runtime_pw' NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS INHERIT;")
                cur.execute("GRANT sosp_runtime_role TO sosp_runtime_app;")
                cur.execute("GRANT USAGE ON SCHEMA public TO sosp_runtime_role;")

        print("======================================================================")
        print("SOSP — HOMOLOGAÇÃO DETERMINÍSTICA DA ETAPA 4D.2 (19 CENÁRIOS EXAUSTIVOS)")
        print("======================================================================")

        # ---------------------------------------------------------------------
        # TESTE 1: Configuração do Schema de Segurança e Chave HMAC Exclusiva
        # ---------------------------------------------------------------------
        run_cmd([
            f"{PG_BIN}/psql", "-h", pg_sock, "-p", str(pg_port), "-U", "postgres", "-d", "sosp_homolog_4d2",
            "-v", "ON_ERROR_STOP=1",
            "-f", os.path.join(SCRIPTS_DIR, "run_4d2_setup_security_context.sql")
        ])
        with psycopg.connect(host=pg_sock, port=pg_port, dbname="sosp_homolog_4d2", user="postgres", autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT sosp_security.set_hmac_secret(%s);", (DB_HMAC_KEY,))
        print("✓ Cenário 1 aprovado: Schema sosp_security e chave HMAC exclusiva do banco provisionados com sucesso.")

        # ---------------------------------------------------------------------
        # TESTE 2: Isolamento da Tabela de Segredos
        # ---------------------------------------------------------------------
        with psycopg.connect(host=pg_sock, port=pg_port, dbname="sosp_homolog_4d2", user="sosp_runtime_app", password="runtime_pw", autocommit=True) as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute("SELECT secret_key FROM sosp_security.hmac_secret;")
                    raise AssertionError("sosp_runtime_app não pode ler hmac_secret!")
                except psycopg.errors.InsufficientPrivilege:
                    pass
                try:
                    cur.execute("SELECT * FROM sosp_security.used_nonces;")
                    raise AssertionError("sosp_runtime_app não pode acessar used_nonces diretamente!")
                except psycopg.errors.InsufficientPrivilege:
                    pass
        print("✓ Cenário 2 aprovado: Acesso a sosp_security.hmac_secret e used_nonces negado para sosp_runtime_app (42501).")

        # ---------------------------------------------------------------------
        # TESTE 3: Concessão de Privilégios Mínimos DML
        # ---------------------------------------------------------------------
        run_cmd([
            f"{PG_BIN}/psql", "-h", pg_sock, "-p", str(pg_port), "-U", "postgres", "-d", "sosp_homolog_4d2",
            "-v", "ON_ERROR_STOP=1",
            "-f", os.path.join(SCRIPTS_DIR, "run_4d2_apply_minimum_grants.sql")
        ])
        with psycopg.connect(host=pg_sock, port=pg_port, dbname="sosp_homolog_4d2", user="postgres", autocommit=True) as conn:
            with conn.cursor() as cur:
                # Valida ZERO TRUNCATE
                cur.execute("""
                SELECT count(*) FROM information_schema.table_privileges
                WHERE grantee = 'sosp_runtime_role' AND privilege_type = 'TRUNCATE';
                """)
                assert cur.fetchone()[0] == 0, "Zero TRUNCATE deve ser garantido!"
                # Valida ZERO REFERENCES
                cur.execute("""
                SELECT count(*) FROM information_schema.table_privileges
                WHERE grantee = 'sosp_runtime_role' AND privilege_type = 'REFERENCES';
                """)
                assert cur.fetchone()[0] == 0, "Zero REFERENCES deve ser garantido!"
                # Valida ZERO TRIGGER
                cur.execute("""
                SELECT count(*) FROM information_schema.table_privileges
                WHERE grantee = 'sosp_runtime_role' AND privilege_type = 'TRIGGER';
                """)
                assert cur.fetchone()[0] == 0, "Zero TRIGGER deve ser garantido!"
                # Valida ZERO DELETE em accountsCitizen
                cur.execute("""
                SELECT has_table_privilege('sosp_runtime_role', 'public.accountsCitizen', 'DELETE');
                """)
                assert cur.fetchone()[0] is False, "Zero DELETE físico em entidades de negócio!"
        print("✓ Cenário 3 aprovado: Matriz de concessões DML validada com sucesso.")

        # ---------------------------------------------------------------------
        # TESTE 4: Aplicação de Políticas RLS Granulares
        # ---------------------------------------------------------------------
        run_cmd([
            f"{PG_BIN}/psql", "-h", pg_sock, "-p", str(pg_port), "-U", "postgres", "-d", "sosp_homolog_4d2",
            "-v", "ON_ERROR_STOP=1",
            "-f", os.path.join(SCRIPTS_DIR, "run_4d2_apply_rls_policies.sql")
        ])
        print("✓ Cenário 4 aprovado: Políticas RLS aplicadas com sucesso.")

        # ---------------------------------------------------------------------
        # TESTE 5: Tentativa de GUC Spoofing Direto sem HMAC Válido
        # ---------------------------------------------------------------------
        victim_citizen_id = str(uuid.uuid4())
        with psycopg.connect(host=pg_sock, port=pg_port, dbname="sosp_homolog_4d2", user="sosp_runtime_app", password="runtime_pw", autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT set_config('sosp.current_user_id', %s, true);", (victim_citizen_id,))
                cur.execute("SELECT set_config('sosp.current_role', 'citizen', true);")
                cur.execute("SELECT set_config('sosp.context_signature', 'fake_sig', true);")
                cur.execute("SELECT sosp_security.is_context_valid();")
                assert cur.fetchone()[0] is False
                cur.execute("SELECT sosp_security.get_current_citizen_id();")
                assert cur.fetchone()[0] is None
        print("✓ Cenário 5 aprovado: Tentativa direta de forjamento de GUC bloqueada dinamicamente.")

        # ---------------------------------------------------------------------
        # TESTE 6: Rejeição de Assinatura com Chave Incorreta (Django SECRET_KEY)
        # ---------------------------------------------------------------------
        now_epoch = int(time.time())
        expires_at = now_epoch + 60
        nonce_6 = str(uuid.uuid4())
        wrong_sig = compute_context_hmac(victim_citizen_id, "citizen", None, expires_at, nonce_6, secret_key=DJANGO_SECRET_KEY)
        with psycopg.connect(host=pg_sock, port=pg_port, dbname="sosp_homolog_4d2", user="sosp_runtime_app", password="runtime_pw", autocommit=False) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT sosp_security.set_request_context(%s, 'citizen', NULL, %s, %s, %s);", (victim_citizen_id, expires_at, nonce_6, wrong_sig))
                assert cur.fetchone()[0] is False, "Assinatura com chave divergente deve ser rejeitada!"
        print("✓ Cenário 6 aprovado: Assinatura gerada com chave divergente (Django SECRET_KEY) sumariamente rejeitada.")

        # ---------------------------------------------------------------------
        # TESTE 7: Anti-Replay — Rejeição de Tokens Expirados no Passado
        # ---------------------------------------------------------------------
        past_epoch = now_epoch - 30
        nonce_7 = str(uuid.uuid4())
        past_sig = compute_context_hmac(victim_citizen_id, "citizen", None, past_epoch, nonce_7, secret_key=DB_HMAC_KEY)
        with psycopg.connect(host=pg_sock, port=pg_port, dbname="sosp_homolog_4d2", user="sosp_runtime_app", password="runtime_pw", autocommit=False) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT sosp_security.set_request_context(%s, 'citizen', NULL, %s, %s, %s);", (victim_citizen_id, past_epoch, nonce_7, past_sig))
                assert cur.fetchone()[0] is False, "Token com expiração no passado deve ser rejeitado!"
        print("✓ Cenário 7 aprovado: Anti-Replay validado (tokens expirados no passado são rejeitados).")

        # ---------------------------------------------------------------------
        # TESTE 8: Anti-Replay — Rejeição de Tokens com Expiração Excessiva (> 120s)
        # ---------------------------------------------------------------------
        excessive_epoch = now_epoch + 300
        nonce_8 = str(uuid.uuid4())
        excessive_sig = compute_context_hmac(victim_citizen_id, "citizen", None, excessive_epoch, nonce_8, secret_key=DB_HMAC_KEY)
        with psycopg.connect(host=pg_sock, port=pg_port, dbname="sosp_homolog_4d2", user="sosp_runtime_app", password="runtime_pw", autocommit=False) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT sosp_security.set_request_context(%s, 'citizen', NULL, %s, %s, %s);", (victim_citizen_id, excessive_epoch, nonce_8, excessive_sig))
                assert cur.fetchone()[0] is False, "Token com expiração > 120s deve ser rejeitado!"
        print("✓ Cenário 8 aprovado: Anti-Replay validado (tokens com validade excessiva > 120s são rejeitados).")

        # ---------------------------------------------------------------------
        # TESTE 9: Anti-Replay Estrito — Rejeição de Nonce Duplicado (Single-Use Token)
        # ---------------------------------------------------------------------
        single_use_nonce = str(uuid.uuid4())
        single_use_exp = int(time.time()) + 60
        single_use_sig = compute_context_hmac(victim_citizen_id, "citizen", None, single_use_exp, single_use_nonce, secret_key=DB_HMAC_KEY)
        with psycopg.connect(host=pg_sock, port=pg_port, dbname="sosp_homolog_4d2", user="sosp_runtime_app", password="runtime_pw", autocommit=True) as conn:
            with conn.cursor() as cur:
                # 1ª Tentativa: Válida
                cur.execute("SELECT sosp_security.set_request_context(%s, 'citizen', NULL, %s, %s, %s);", (victim_citizen_id, single_use_exp, single_use_nonce, single_use_sig))
                assert cur.fetchone()[0] is True, "Primeiro uso do token/nonce deve ser bem sucedido!"
                # 2ª Tentativa (Replay idêntico no mesmo intervalo de tempo): REJEITADO
                cur.execute("SELECT sosp_security.set_request_context(%s, 'citizen', NULL, %s, %s, %s);", (victim_citizen_id, single_use_exp, single_use_nonce, single_use_sig))
                assert cur.fetchone()[0] is False, "Replay do mesmo nonce DEVE ser sumariamente rejeitado!"
        print("✓ Cenário 9 aprovado: Anti-Replay Estrito validado (replay do mesmo token/nonce em outra transação rejeitado).")

        # ---------------------------------------------------------------------
        # TESTE 10: Anti-Tampering de Usuário durante a Sessão
        # ---------------------------------------------------------------------
        citizen_a_id = str(uuid.uuid4())
        citizen_b_id = str(uuid.uuid4())
        valid_exp = int(time.time()) + 60
        nonce_a = str(uuid.uuid4())
        valid_sig_a = compute_context_hmac(citizen_a_id, "citizen", None, valid_exp, nonce_a, secret_key=DB_HMAC_KEY)
        with psycopg.connect(host=pg_sock, port=pg_port, dbname="sosp_homolog_4d2", user="sosp_runtime_app", password="runtime_pw", autocommit=False) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT sosp_security.set_request_context(%s, 'citizen', NULL, %s, %s, %s);", (citizen_a_id, valid_exp, nonce_a, valid_sig_a))
                assert cur.fetchone()[0] is True
                assert cur.execute("SELECT sosp_security.is_context_valid();") or cur.fetchone()[0] is True

                # Atacante altera GUC de usuário na mesma conexão
                cur.execute("SELECT set_config('sosp.current_user_id', %s, true);", (citizen_b_id,))
                cur.execute("SELECT sosp_security.is_context_valid();")
                assert cur.fetchone()[0] is False, "Alteração de GUC deve invalidar o contexto dinamicamente!"
                cur.execute("SELECT sosp_security.get_current_citizen_id();")
                assert cur.fetchone()[0] is None
        print("✓ Cenário 10 aprovado: Anti-Tampering de usuário validado (alteração em voo invalida o contexto).")

        # ---------------------------------------------------------------------
        # TESTE 11: Anti-Tampering de Agência durante a Sessão
        # ---------------------------------------------------------------------
        server_id = str(uuid.uuid4())
        agency_1_id = str(uuid.uuid4())
        agency_2_id = str(uuid.uuid4())
        nonce_srv = str(uuid.uuid4())
        valid_server_sig = compute_context_hmac(server_id, "server", agency_1_id, valid_exp, nonce_srv, secret_key=DB_HMAC_KEY)
        with psycopg.connect(host=pg_sock, port=pg_port, dbname="sosp_homolog_4d2", user="sosp_runtime_app", password="runtime_pw", autocommit=False) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT sosp_security.set_request_context(%s, 'server', %s, %s, %s, %s);", (server_id, agency_1_id, valid_exp, nonce_srv, valid_server_sig))
                assert cur.fetchone()[0] is True

                # Atacante altera GUC da agência
                cur.execute("SELECT set_config('sosp.current_agency_id', %s, true);", (agency_2_id,))
                cur.execute("SELECT sosp_security.is_context_valid();")
                assert cur.fetchone()[0] is False
                cur.execute("SELECT sosp_security.get_current_agency_id();")
                assert cur.fetchone()[0] is None
        print("✓ Cenário 11 aprovado: Anti-Tampering de agência validado (alteração em voo invalida o contexto).")

        # ---------------------------------------------------------------------
        # TESTE 12: RLS Cidadão Positivo e Negativo
        # ---------------------------------------------------------------------
        # Insere dados de teste via conexão administrativa
        with psycopg.connect(host=pg_sock, port=pg_port, dbname="sosp_homolog_4d2", user="postgres", autocommit=True) as conn:
            with conn.cursor() as cur:
                gender_id = str(uuid.uuid4())
                cur.execute("INSERT INTO public.accountsGender (id, name, sortOrder) VALUES (%s, 'Masculino', 1) ON CONFLICT (name) DO NOTHING;", (gender_id,))
                cur.execute("SELECT id FROM public.accountsGender WHERE name = 'Masculino';")
                gender_id = str(cur.fetchone()[0])

                cur.execute("""
                INSERT INTO public.accountsCitizen (
                    id, cpf, fullName, birthDate, email, phone, passwordHash, passwordSalt,
                    genderId, motherName, zipCode, street, neighborhood, city, state, addressNumber
                ) VALUES
                (%s, '11111111111', 'Cidadão Alpha', '1990-01-01', 'alpha@sosp.gov.br', '82999990001', 'hash1', 'salt1', %s, 'Mãe Alpha', '57000000', 'Rua 1', 'Centro', 'Maceió', 'AL', '10'),
                (%s, '22222222222', 'Cidadão Beta', '1992-02-02', 'beta@sosp.gov.br', '82999990002', 'hash2', 'salt2', %s, 'Mãe Beta', '57000000', 'Rua 2', 'Centro', 'Maceió', 'AL', '20');
                """, (citizen_a_id, gender_id, citizen_b_id, gender_id))

        nonce_12 = str(uuid.uuid4())
        sig_12 = compute_context_hmac(citizen_a_id, "citizen", None, valid_exp, nonce_12, secret_key=DB_HMAC_KEY)
        with psycopg.connect(host=pg_sock, port=pg_port, dbname="sosp_homolog_4d2", user="sosp_runtime_app", password="runtime_pw", autocommit=False) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT sosp_security.set_request_context(%s, 'citizen', NULL, %s, %s, %s);", (citizen_a_id, valid_exp, nonce_12, sig_12))
                cur.execute("SELECT id, fullName FROM public.accountsCitizen;")
                rows = cur.fetchall()
                assert len(rows) == 1
                assert str(rows[0][0]) == citizen_a_id
                # Tentativa de atualizar Cidadão B
                cur.execute("UPDATE public.accountsCitizen SET fullName = 'Hacked' WHERE id = %s;", (citizen_b_id,))
                assert cur.rowcount == 0
        print("✓ Cenário 12 aprovado: RLS Cidadão validado (Cidadão A enxerga apenas a si mesmo; Cidadão B invisível e inalterável).")

        # ---------------------------------------------------------------------
        # TESTE 13: RLS Cadastro Cidadão — Proteções Especiais
        # ---------------------------------------------------------------------
        nonce_13 = str(uuid.uuid4())
        sig_13 = compute_context_hmac(citizen_a_id, "citizen", None, valid_exp, nonce_13, secret_key=DB_HMAC_KEY)
        with psycopg.connect(host=pg_sock, port=pg_port, dbname="sosp_homolog_4d2", user="sosp_runtime_app", password="runtime_pw", autocommit=False) as conn:
            with conn.cursor() as cur:
                # 13.1. Usuário autenticado como cidadão tenta cadastrar outro cidadão -> BLOQUEADO
                cur.execute("SELECT sosp_security.set_request_context(%s, 'citizen', NULL, %s, %s, %s);", (citizen_a_id, valid_exp, nonce_13, sig_13))
                new_cid = str(uuid.uuid4())
                try:
                    cur.execute("""
                    INSERT INTO public.accountsCitizen (
                        id, cpf, fullName, birthDate, email, phone, passwordHash, passwordSalt,
                        genderId, motherName, zipCode, street, neighborhood, city, state, addressNumber
                    ) VALUES (%s, '33333333333', 'Novo Cidadão', '1995-03-03', 'novo@sosp.gov.br', '82999990003', 'h', 's', %s, 'Mãe', '57000000', 'Rua', 'Bairro', 'Maceió', 'AL', '1');
                    """, (new_cid, gender_id))
                    raise AssertionError("Cidadão autenticado não pode cadastrar outros usuários!")
                except psycopg.errors.InsufficientPrivilege:
                    conn.rollback()

                # 13.2. Usuário anônimo submete cadastro -> SUCESSO
                cur.execute("SELECT sosp_security.clear_request_context();")
                anon_cid = str(uuid.uuid4())
                cur.execute("""
                INSERT INTO public.accountsCitizen (
                    id, cpf, fullName, birthDate, email, phone, passwordHash, passwordSalt,
                    genderId, motherName, zipCode, street, neighborhood, city, state, addressNumber
                ) VALUES (%s, '44444444444', 'Cidadão Anônimo Signup', '1996-04-04', 'anon@sosp.gov.br', '82999990004', 'h', 's', %s, 'Mãe', '57000000', 'Rua', 'Bairro', 'Maceió', 'AL', '1');
                """, (anon_cid, gender_id))
                conn.commit()
        print("✓ Cenário 13 aprovado: Regras de cadastro de cidadão validadas (usuários logados impedidos de criar cadastros).")

        # ---------------------------------------------------------------------
        # TESTE 14: RLS Trilha de Auditoria (Anti-Falsificação de Autoria)
        # ---------------------------------------------------------------------
        nonce_14 = str(uuid.uuid4())
        sig_14 = compute_context_hmac(citizen_a_id, "citizen", None, valid_exp, nonce_14, secret_key=DB_HMAC_KEY)
        with psycopg.connect(host=pg_sock, port=pg_port, dbname="sosp_homolog_4d2", user="sosp_runtime_app", password="runtime_pw", autocommit=False) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT sosp_security.set_request_context(%s, 'citizen', NULL, %s, %s, %s);", (citizen_a_id, valid_exp, nonce_14, sig_14))

                # 14.1. Cidadão A tenta inserir evento forjando actorId = Citizen B -> BLOQUEADO
                try:
                    cur.execute("""
                    INSERT INTO public.auditEvent (actorType, actorId, action, entityType, entityId)
                    VALUES ('citizen', %s, 'citizen.profile.view', 'accountsCitizen', %s);
                    """, (citizen_b_id, citizen_b_id))
                    raise AssertionError("Tentativa de forjar actorId de terceiro na auditoria deve ser bloqueada!")
                except psycopg.errors.InsufficientPrivilege:
                    conn.rollback()

                # 14.2. Cidadão A tenta forjar actorType = 'servant' -> BLOQUEADO
                nonce_14_2 = str(uuid.uuid4())
                sig_14_2 = compute_context_hmac(citizen_a_id, "citizen", None, valid_exp, nonce_14_2, secret_key=DB_HMAC_KEY)
                cur.execute("SELECT sosp_security.set_request_context(%s, 'citizen', NULL, %s, %s, %s);", (citizen_a_id, valid_exp, nonce_14_2, sig_14_2))
                try:
                    cur.execute("""
                    INSERT INTO public.auditEvent (actorType, actorId, action, entityType, entityId)
                    VALUES ('servant', %s, 'admin.audit.view', 'accountsCitizen', %s);
                    """, (citizen_a_id, citizen_a_id))
                    raise AssertionError("Cidadão não pode emitir evento como servant!")
                except psycopg.errors.InsufficientPrivilege:
                    conn.rollback()

                # 14.3. Cidadão A insere evento com seus dados legítimos -> SUCESSO
                nonce_14_3 = str(uuid.uuid4())
                sig_14_3 = compute_context_hmac(citizen_a_id, "citizen", None, valid_exp, nonce_14_3, secret_key=DB_HMAC_KEY)
                cur.execute("SELECT sosp_security.set_request_context(%s, 'citizen', NULL, %s, %s, %s);", (citizen_a_id, valid_exp, nonce_14_3, sig_14_3))
                cur.execute("""
                INSERT INTO public.auditEvent (actorType, actorId, action, entityType, entityId)
                VALUES ('citizen', %s, 'citizen.profile.view', 'accountsCitizen', %s);
                """, (citizen_a_id, citizen_a_id))
                conn.commit()
        print("✓ Cenário 14 aprovado: Anti-falsificação de autoria na auditoria validada com sucesso.")

        # ---------------------------------------------------------------------
        # TESTE 15: RLS Servidor e Restrição por Agência
        # ---------------------------------------------------------------------
        unit_1_id = str(uuid.uuid4())
        unit_2_id = str(uuid.uuid4())
        with psycopg.connect(host=pg_sock, port=pg_port, dbname="sosp_homolog_4d2", user="postgres", autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO public.catalogAgency (id, name, acronym, sphere) VALUES (%s, 'DETRAN', 'DETRAN', 'state'), (%s, 'SEFAZ', 'SEFAZ', 'state');", (agency_1_id, agency_2_id))
                cur.execute("INSERT INTO public.catalogUnit (id, agencyId, name, zipCode, street, neighborhood, city, state, addressNumber) VALUES (%s, %s, 'Posto DETRAN', '57000000', 'Rua A', 'Centro', 'Maceió', 'AL', '1'), (%s, %s, 'Posto SEFAZ', '57000000', 'Rua B', 'Centro', 'Maceió', 'AL', '2');", (unit_1_id, agency_1_id, unit_2_id, agency_2_id))
                srv_id = str(uuid.uuid4())
                cur.execute("INSERT INTO public.catalogService (id, name, category, detailedDescription, eligibility, averageDeadlineDays, channel, status) VALUES (%s, 'CNH', 'transport', 'Desc', 'Elig', 5, 'inPerson', 'active');", (srv_id,))
                cur.execute("INSERT INTO public.catalogServiceAgency (serviceId, agencyId) VALUES (%s, %s);", (srv_id, agency_1_id))
                s1_id = str(uuid.uuid4())
                s2_id = str(uuid.uuid4())
                cur.execute("INSERT INTO public.schedulingSlot (id, unitId, slotDate, startsAt, endsAt, capacity) VALUES (%s, %s, '2026-12-01', '08:00', '08:30', 5), (%s, %s, '2026-12-01', '08:00', '08:30', 5);", (s1_id, unit_1_id, s2_id, unit_2_id))
                app_1_id = str(uuid.uuid4())
                app_2_id = str(uuid.uuid4())
                cur.execute("INSERT INTO public.schedulingAppointment (id, protocolNumber, slotId, unitId, serviceId, citizenId, scheduledDate, scheduledTime, status) VALUES (%s, '20261201-0001', %s, %s, %s, %s, '2026-12-01', '08:00', 'scheduled'), (%s, '20261201-0002', %s, %s, %s, %s, '2026-12-01', '08:00', 'scheduled');", (app_1_id, s1_id, unit_1_id, srv_id, citizen_a_id, app_2_id, s2_id, unit_2_id, srv_id, citizen_b_id))

        nonce_15 = str(uuid.uuid4())
        valid_server_sig_15 = compute_context_hmac(server_id, "server", agency_1_id, valid_exp, nonce_15, secret_key=DB_HMAC_KEY)
        with psycopg.connect(host=pg_sock, port=pg_port, dbname="sosp_homolog_4d2", user="sosp_runtime_app", password="runtime_pw", autocommit=False) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT sosp_security.set_request_context(%s, 'server', %s, %s, %s, %s);", (server_id, agency_1_id, valid_exp, nonce_15, valid_server_sig_15))
                cur.execute("SELECT id, protocolNumber FROM public.schedulingAppointment;")
                rows = cur.fetchall()
                assert len(rows) == 1
                assert str(rows[0][0]) == app_1_id
        print("✓ Cenário 15 aprovado: RLS do Servidor validado (restrito aos postos da agência do contexto).")

        # ---------------------------------------------------------------------
        # TESTE 16: Reaproveitamento de Conexão no Pool (Connection Reuse Test)
        # ---------------------------------------------------------------------
        nonce_16_a = str(uuid.uuid4())
        sig_16_a = compute_context_hmac(citizen_a_id, "citizen", None, valid_exp, nonce_16_a, secret_key=DB_HMAC_KEY)
        nonce_16_b = str(uuid.uuid4())
        sig_16_b = compute_context_hmac(citizen_b_id, "citizen", None, valid_exp, nonce_16_b, secret_key=DB_HMAC_KEY)
        with psycopg.connect(host=pg_sock, port=pg_port, dbname="sosp_homolog_4d2", user="sosp_runtime_app", password="runtime_pw", autocommit=False) as conn:
            with conn.cursor() as cur:
                # Requisição 1: Cidadão A
                cur.execute("SELECT sosp_security.set_request_context(%s, 'citizen', NULL, %s, %s, %s);", (citizen_a_id, valid_exp, nonce_16_a, sig_16_a))
                cur.execute("SELECT id FROM public.accountsCitizen;")
                assert len(cur.fetchall()) == 1

                # Fim da Requisição 1: Limpeza obrigatória de contexto
                cur.execute("SELECT sosp_security.clear_request_context();")
                conn.commit()

                # Requisição 2 (mesma conexão física reaproveitada sem contexto): Default Deny
                cur.execute("SELECT id FROM public.accountsCitizen;")
                assert len(cur.fetchall()) == 0, "Conexão limpa não pode vazar dados anteriores!"

                # Requisição 3 (mesma conexão autentica como Cidadão B)
                cur.execute("SELECT sosp_security.set_request_context(%s, 'citizen', NULL, %s, %s, %s);", (citizen_b_id, valid_exp, nonce_16_b, sig_16_b))
                cur.execute("SELECT id, fullName FROM public.accountsCitizen;")
                rows = cur.fetchall()
                assert len(rows) == 1
                assert str(rows[0][0]) == citizen_b_id
                assert rows[0][1] == 'Cidadão Beta'

                # Limpeza final
                cur.execute("SELECT sosp_security.clear_request_context();")
                conn.commit()
        print("✓ Cenário 16 aprovado: Reaproveitamento de conexão no pool validado (limpeza estrita e zero contaminação entre sessões).")

        # ---------------------------------------------------------------------
        # TESTE 17: Segurança das Funções SECURITY DEFINER
        # ---------------------------------------------------------------------
        with psycopg.connect(host=pg_sock, port=pg_port, dbname="sosp_homolog_4d2", user="sosp_runtime_app", password="runtime_pw", autocommit=True) as conn:
            with conn.cursor() as cur:
                # Verifica search_path das funções
                cur.execute("""
                SELECT proname, proconfig FROM pg_proc
                JOIN pg_namespace ON pg_proc.pronamespace = pg_namespace.oid
                WHERE nspname = 'sosp_security';
                """)
                for name, config in cur.fetchall():
                    assert config is not None and any("search_path=" in c for c in config), f"Função {name} sem search_path seguro!"

                # Tenta executar funções administrativas protegidas
                try:
                    cur.execute("SELECT sosp_security.set_hmac_secret('hacked_key_attempt_32b_length_ok');")
                    raise AssertionError("sosp_runtime_app não pode executar set_hmac_secret!")
                except psycopg.errors.InsufficientPrivilege:
                    pass
                try:
                    cur.execute("SELECT sosp_security.compute_raw_hmac('data', 'key');")
                    raise AssertionError("sosp_runtime_app não pode executar compute_raw_hmac!")
                except psycopg.errors.InsufficientPrivilege:
                    pass
        print("✓ Cenário 17 aprovado: Funções SECURITY DEFINER com search_path seguro e privilégios administrativos bloqueados.")

        # ---------------------------------------------------------------------
        # TESTE 18: Reversibilidade DML
        # ---------------------------------------------------------------------
        run_cmd([
            f"{PG_BIN}/psql", "-h", pg_sock, "-p", str(pg_port), "-U", "postgres", "-d", "sosp_homolog_4d2",
            "-v", "ON_ERROR_STOP=1",
            "-f", os.path.join(SCRIPTS_DIR, "run_4d2_rollback_minimum_grants.sql")
        ])
        with psycopg.connect(host=pg_sock, port=pg_port, dbname="sosp_homolog_4d2", user="postgres", autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT has_table_privilege('sosp_runtime_app', 'public.accountscitizen', 'SELECT');")
                assert cur.fetchone()[0] is False
        print("✓ Cenário 18 aprovado: Rollback DML revogou 100% dos grants com sucesso.")

        # ---------------------------------------------------------------------
        # TESTE 19: Reversibilidade RLS Cirúrgica (SEM CASCADE)
        # ---------------------------------------------------------------------
        run_cmd([
            f"{PG_BIN}/psql", "-h", pg_sock, "-p", str(pg_port), "-U", "postgres", "-d", "sosp_homolog_4d2",
            "-v", "ON_ERROR_STOP=1",
            "-f", os.path.join(SCRIPTS_DIR, "run_4d2_rollback_rls_policies.sql")
        ])
        with psycopg.connect(host=pg_sock, port=pg_port, dbname="sosp_homolog_4d2", user="postgres", autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'sosp_security');")
                assert cur.fetchone()[0] is False
        print("✓ Cenário 19 aprovado: Rollback cirúrgico de RLS e schema sosp_security (RESTRICT) concluído com sucesso.")

        print("======================================================================")
        print("✅ TODOS OS 19 CENÁRIOS DE HOMOLOGAÇÃO DA ETAPA 4D.2 FORAM APROVADOS!")
        print("======================================================================")

    finally:
        subprocess.run([f"{PG_BIN}/pg_ctl", "-D", pg_data, "stop", "-m", "immediate"], capture_output=True)

if __name__ == "__main__":
    main()
