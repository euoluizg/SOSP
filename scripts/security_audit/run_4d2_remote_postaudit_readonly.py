#!/usr/bin/env python3
"""
SOSP — ETAPA 4D.2: AUDITORIA PÓS-COMMIT REMOTA (READ ONLY)
Execução: Terminal interativo do proprietário (@euoluizg).
Garantias e Verificações Obrigatórias:
1. Conexão estritamente READ ONLY com a identidade de aplicação (sosp_runtime_app) e TLS verify-full.
2. Identidade de runtime do Session Pooler: estritamente 'sosp_runtime_app.<PROJECT_REF>' (ex.: sosp_runtime_app.cidtcgfowvgwgggvhbym).
3. Rejeição explícita de formatos invertidos ('<PROJECT_REF>.sosp_runtime_app') e de outros projetos.
4. Validação de destino homologado: host 'aws-1-sa-east-1.pooler.supabase.com', porta 5432, banco 'postgres'.
5. Auditoria 100% em leitura (zero DML, zero mutação em nonces ou dados).
6. Homologação de Default Deny (sem contexto, 0 linhas retornadas em accountscitizen via RLS).
7. Homologação de Mínimo Privilégio via has_table_privilege no catálogo físico (zero DELETE, zero TRUNCATE).
8. Homologação de Isolamento de Segredos (acesso estritamente negado em sosp_security.hmac_secret e used_nonces).
9. Homologação de Isolamento de Funções Criptográficas (set_hmac_secret e compute_raw_hmac bloqueados).
10. Homologação de Views com security_invoker = true no catálogo físico (pg_class.relname canônico).
"""

import sys
import os
import getpass
import psycopg
from psycopg import sql

# Importa o módulo central de validação de identidade e inventário físico
SCRATCH_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRATCH_DIR not in sys.path:
    sys.path.insert(0, SCRATCH_DIR)

from sosp_remote_pooler_identity import (
    AUTHORIZED_PROJECT_REF,
    DEFAULT_POOLER_HOST,
    DEFAULT_POOLER_PORT,
    DEFAULT_DBNAME,
    PHYSICAL_38_TABLES,
    PHYSICAL_2_VIEWS,
    PHYSICAL_40_OBJECTS,
    validate_runtime_user,
    validate_pooler_destination,
    validate_tls_params,
)

def read_input(prompt_text: str, default: str = "") -> str:
    try:
        with open("/dev/tty", "r") as tty_in, open("/dev/tty", "w") as tty_out:
            tty_out.write(prompt_text)
            tty_out.flush()
            line = tty_in.readline()
            if not line:
                return default
            res = line.strip()
            return res if res else default
    except (OSError, IOError):
        if sys.stdin.isatty():
            res = input(prompt_text).strip()
            return res if res else default
        raise RuntimeError("Terminal interativo (/dev/tty) não disponível.")

def read_password(prompt_text: str) -> str:
    try:
        return getpass.getpass(prompt_text)
    except (OSError, IOError, EOFError) as e:
        raise RuntimeError(f"Falha ao ler senha: {e}")

def configure_ssl_params() -> dict:
    env_ca = os.getenv("PGSSLROOTCERT", "").strip()
    if env_ca:
        expanded = os.path.expanduser(env_ca)
        if not os.path.isfile(expanded) or not os.access(expanded, os.R_OK):
            sys.exit(f"❌ ABORTO: PGSSLROOTCERT ({env_ca}) não acessível.")
        return validate_tls_params({"sslmode": "verify-full", "sslrootcert": expanded})

    home_ca = os.path.expanduser("~/.sosp-certificates/supabase-ca.crt")
    if os.path.isfile(home_ca) and os.access(home_ca, os.R_OK):
        return validate_tls_params({"sslmode": "verify-full", "sslrootcert": home_ca})

    for sys_ca in ["/etc/ssl/cert.pem", "/etc/ssl/certs/ca-certificates.crt"]:
        if os.path.isfile(sys_ca) and os.access(sys_ca, os.R_OK):
            return validate_tls_params({"sslmode": "verify-full", "sslrootcert": sys_ca})

    sys.exit("❌ ABORTO: Nenhuma autoridade certificadora confiável encontrada para verify-full.")

def main():
    print("=" * 80)
    print("SOSP — ETAPA 4D.2: AUDITORIA PÓS-COMMIT REMOTA (READ ONLY)")
    print("=" * 80)

    ssl_params = configure_ssl_params()

    # Validação do destino homologado
    try:
        host, port, db = validate_pooler_destination(DEFAULT_POOLER_HOST, DEFAULT_POOLER_PORT, DEFAULT_DBNAME)
    except ValueError as err:
        sys.exit(f"❌ ABORTO: Destino inválido: {err}")

    print(f"• Destino Homologado : {host}:{port} (Banco: {db})")
    print(f"• TLS Modo           : {ssl_params['sslmode']} (CA: {ssl_params['sslrootcert']})")
    print(f"• Identidade Alvo    : sosp_runtime_app.{AUTHORIZED_PROJECT_REF}\n")

    # Prompt do usuário de runtime com padrão e validação estrita 'sosp_runtime_app.<project-ref>'
    expected_default_runtime = f"sosp_runtime_app.{AUTHORIZED_PROJECT_REF}"
    runtime_user_input = read_input(f"Usuário de runtime [{expected_default_runtime}]: ", expected_default_runtime)
    try:
        runtime_user = validate_runtime_user(runtime_user_input)
    except ValueError as err:
        sys.exit(f"❌ ABORTO: {err}")

    print(f"✓ Identidade de runtime validada: {runtime_user}")

    runtime_pass = read_password(f"Senha de {runtime_user} (entrada oculta): ")
    if not runtime_pass:
        sys.exit("❌ ABORTO: Senha não pode ser vazia.")

    conn_params = {
        "host": host,
        "port": port,
        "dbname": db,
        "user": runtime_user,
        "password": runtime_pass,
        "connect_timeout": 15,
        "autocommit": True,
        **ssl_params
    }

    try:
        print("\n[1/6] Conectando como sosp_runtime_app sob transação estritamente READ ONLY...")
        with psycopg.connect(**conn_params) as conn:
            if not conn.pgconn.ssl_in_use:
                sys.exit("❌ ABORTO DE SEGURANÇA: Conexão TLS não foi ativada pelo servidor!")

            with conn.cursor() as cur:
                cur.execute("BEGIN READ ONLY;")
                cur.execute("SHOW transaction_read_only;")
                ro = cur.fetchone()[0]
                if ro != "on":
                    sys.exit(f"❌ ABORTO DE SEGURANÇA: transaction_read_only esperava 'on', obtido '{ro}'.")
                print("✓ Transação READ ONLY confirmada como sosp_runtime_app.")

                # 1. Atributos da role conectada
                cur.execute("SELECT current_user, session_user;")
                c_usr, s_usr = cur.fetchone()
                print(f"• Conectado como: current_user={c_usr} | session_user={s_usr}")

                # Teste 1: Default Deny via RLS
                print("\n[2/6] Auditando Default Deny em tabelas privadas (sem contexto estabelecido)...")
                cur.execute("SELECT count(*) FROM public.accountscitizen;")
                citizen_count = cur.fetchone()[0]
                print(f"• Linhas visíveis em accountscitizen sem contexto: {citizen_count} (esperado: 0)")
                assert citizen_count == 0, "Falha de segurança: Default Deny não filtrou accountscitizen!"
                print("✓ Default Deny validado com sucesso via RLS.")

                # Teste 2: Mínimos Privilégios DML nas tabelas de negócio físicas
                print("\n[3/6] Auditando matriz de mínimos privilégios DML via catálogo físico...")
                cur.execute("""
                SELECT
                    has_table_privilege('sosp_runtime_role', 'public.accountscitizen', 'SELECT'),
                    has_table_privilege('sosp_runtime_role', 'public.accountscitizen', 'INSERT'),
                    has_table_privilege('sosp_runtime_role', 'public.accountscitizen', 'UPDATE'),
                    has_table_privilege('sosp_runtime_role', 'public.accountscitizen', 'DELETE'),
                    has_table_privilege('sosp_runtime_role', 'public.accountscitizen', 'TRUNCATE');
                """)
                can_sel, can_ins, can_upd, can_del, can_trunc = cur.fetchone()
                print(f"• accountscitizen: SELECT={can_sel}, INSERT={can_ins}, UPDATE={can_upd}, DELETE={can_del}, TRUNCATE={can_trunc}")
                assert can_sel and can_ins and can_upd, "Falha: privilégios de negócio não concedidos!"
                assert not can_del and not can_trunc, "Falha de segurança: DELETE ou TRUNCATE permitido em accountscitizen (violação RN-40)!"
                print("✓ Privilégios DML mínimos confirmados (zero DELETE, zero TRUNCATE).")

                # Teste 3: Isolamento de Tabelas Secretas (sosp_security)
                print("\n[4/6] Auditando isolamento de tabelas secretas...")
                cur.execute("""
                SELECT
                    has_table_privilege('sosp_runtime_app', 'sosp_security.hmac_secret', 'SELECT'),
                    has_table_privilege('sosp_runtime_app', 'sosp_security.used_nonces', 'SELECT');
                """)
                can_see_secret, can_see_nonces = cur.fetchone()
                print(f"• sosp_security.hmac_secret visível? {can_see_secret} (esperado: False)")
                print(f"• sosp_security.used_nonces visível? {can_see_nonces} (esperado: False)")
                assert not can_see_secret and not can_see_nonces, "Falha de segurança: sosp_runtime_app possui acesso a tabelas secretas!"
                print("✓ Tabelas criptográficas estritamente isoladas.")

                # Teste 4: Isolamento de Funções Criptográficas
                print("\n[5/6] Auditando privilégios de execução em funções de segurança...")
                cur.execute("""
                SELECT
                    has_function_privilege('sosp_runtime_app', 'sosp_security.set_request_context(uuid, varchar, uuid, bigint, uuid, varchar)', 'EXECUTE'),
                    has_function_privilege('sosp_runtime_app', 'sosp_security.clear_request_context()', 'EXECUTE'),
                    has_function_privilege('sosp_runtime_app', 'sosp_security.is_context_valid()', 'EXECUTE'),
                    has_function_privilege('sosp_runtime_app', 'sosp_security.set_hmac_secret(text)', 'EXECUTE'),
                    has_function_privilege('sosp_runtime_app', 'sosp_security.compute_raw_hmac(text, text)', 'EXECUTE');
                """)
                can_set_ctx, can_clr_ctx, can_chk_ctx, can_set_sec, can_raw_hmac = cur.fetchone()
                print(f"• set_request_context EXECUTE: {can_set_ctx} (esperado: True)")
                print(f"• clear_request_context EXECUTE: {can_clr_ctx} (esperado: True)")
                print(f"• is_context_valid EXECUTE: {can_chk_ctx} (esperado: True)")
                print(f"• set_hmac_secret EXECUTE: {can_set_sec} (esperado: False)")
                print(f"• compute_raw_hmac EXECUTE: {can_raw_hmac} (esperado: False)")
                assert can_set_ctx and can_clr_ctx and can_chk_ctx, "Falha: funções de contexto não concedidas a runtime!"
                assert not can_set_sec and not can_raw_hmac, "Falha de segurança: funções administrativas expostas a runtime!"
                print("✓ Privilégios de funções de segurança homologados com sucesso.")

                # Teste 5: Views com Security Invoker e Total de Políticas
                print("\n[6/6] Auditando views com security_invoker e total de políticas RLS ativas...")
                cur.execute("""
                SELECT c.relname, c.reloptions
                FROM pg_catalog.pg_class c
                JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public'
                  AND c.relname = ANY(%s);
                """, (PHYSICAL_2_VIEWS,))
                for vname, vopts in cur.fetchall():
                    print(f"• View '{vname}': reloptions={vopts}")
                    assert vopts is not None and "security_invoker=true" in vopts, f"View '{vname}' DEVE possuir security_invoker=true garantido!"

                cur.execute("SELECT count(*) FROM pg_policies WHERE schemaname = 'public';")
                policy_count = cur.fetchone()[0]
                print(f"• Total de políticas RLS ativas no schema public: {policy_count}")
                assert policy_count >= 50, f"Esperado >= 50 políticas RLS ativas, obtido {policy_count}!"
                print("✓ Views com security_invoker e políticas ativas validadas.")

                cur.execute("ROLLBACK;")

        print("\n" + "=" * 80)
        print("✅ AUDITORIA PÓS-COMMIT 4D.2 (READ ONLY) CONCLUÍDA COM 100% DE SUCESSO!")
        print("Todas as políticas RLS, privilégios mínimos e proteções de contexto foram confirmadas.")
        print("=" * 80)

    except Exception as e:
        sys.exit(f"❌ FALHA NA AUDITORIA PÓS-COMMIT: {e}")

if __name__ == "__main__":
    main()
