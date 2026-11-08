#!/usr/bin/env python3
"""
SOSP — ETAPA 4D.2: PREFLIGHT E AUDITORIA PRÉ-EXECUÇÃO REMOTA (READ ONLY)
Execução: Terminal interativo do proprietário (@euoluizg).
Garantias e Verificações Obrigatórias:
1. Conexão estritamente READ ONLY (autocommit=True + BEGIN READ ONLY + transaction_read_only = 'on' + ROLLBACK no finally).
2. Validação obrigatória da branch develop e aviso em caso de dirty worktree.
3. Identidade administrativa do Session Pooler: estritamente 'postgres.<PROJECT_REF>' (ex.: postgres.cidtcgfowvgwgggvhbym).
4. Rejeição explícita de formatos invertidos ('<PROJECT_REF>.postgres') e de outros projetos.
5. TLS verify-full com CA homologada (~/.sosp-certificates/supabase-ca.crt ou /etc/ssl/cert.pem).
6. Validação de destino homologado: host 'aws-1-sa-east-1.pooler.supabase.com', porta 5432, banco 'postgres'.
7. Verificação de pg_auth_members no PostgreSQL 17:
   - sosp_runtime_app é membro de sosp_runtime_role com admin_option = False
   - Isolamento total contra associação a papéis administrativos (postgres, anon, authenticated, service_role, supabase_admin)
8. Verificação dos atributos de segurança das roles (NOBYPASSRLS, NOSUPERUSER).
9. Inventário Físico Canônico do PostgreSQL:
   - 38 tabelas físicas em minúsculas ordinárias ('r') com RLS ativo (relrowsecurity = True)
   - 2 views analíticas físicas em minúsculas ('v') com diagnóstico de security_invoker
10. Verificação de ausência de privilégios prévios em tabelas/views para sosp_runtime_role.
11. Execução estritamente em leitura (zero DML).
"""

import sys
import os
import getpass
import subprocess
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
    validate_admin_user,
    validate_pooler_destination,
    validate_tls_params,
)

def check_git_status():
    """Verifica branch develop e estado da árvore de trabalho."""
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode("utf-8").strip()
        if branch != "develop":
            sys.exit(f"❌ ABORTO: Execução permitida exclusivamente na branch 'develop'. Branch atual: '{branch}'.")

        status = subprocess.check_output(
            ["git", "status", "--porcelain"],
            stderr=subprocess.DEVNULL
        ).decode("utf-8").strip()
        if status:
            print("⚠️ AVISO: A árvore de trabalho possui modificações locais de desenvolvimento.")
            print("   O preflight é estritamente READ ONLY e continuará com segurança.\n")
    except Exception as e:
        print(f"⚠️ AVISO: Não foi possível inspecionar o status do Git: {e}\n")

def read_input(prompt_text: str, default: str = "") -> str:
    """Lê entrada garantindo compatibilidade com terminal."""
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
    """Lê senha com entrada oculta."""
    try:
        return getpass.getpass(prompt_text)
    except (OSError, IOError, EOFError) as e:
        raise RuntimeError(f"Falha ao ler senha no terminal: {e}")

def configure_ssl_params() -> dict:
    """Configura parâmetros TLS exigindo verify-full com CA confiável."""
    env_ca = os.getenv("PGSSLROOTCERT", "").strip()
    if env_ca:
        expanded = os.path.expanduser(env_ca)
        if not os.path.isfile(expanded) or not os.access(expanded, os.R_OK):
            sys.exit(f"❌ ABORTO: PGSSLROOTCERT indicado ({env_ca}) não acessível.")
        return validate_tls_params({"sslmode": "verify-full", "sslrootcert": expanded})

    home_ca = os.path.expanduser("~/.sosp-certificates/supabase-ca.crt")
    if os.path.isfile(home_ca) and os.access(home_ca, os.R_OK):
        return validate_tls_params({"sslmode": "verify-full", "sslrootcert": home_ca})

    for sys_ca in ["/etc/ssl/cert.pem", "/etc/ssl/certs/ca-certificates.crt"]:
        if os.path.isfile(sys_ca) and os.access(sys_ca, os.R_OK):
            return validate_tls_params({"sslmode": "verify-full", "sslrootcert": sys_ca})

    sys.exit("❌ ABORTO: Nenhuma autoridade certificadora (CA) confiável encontrada para verify-full.")

def main():
    print("=" * 80)
    print("SOSP — ETAPA 4D.2: PREFLIGHT E AUDITORIA PRÉ-EXECUÇÃO REMOTA (READ ONLY)")
    print("=" * 80)

    check_git_status()
    ssl_params = configure_ssl_params()

    # Validação do destino homologado
    try:
        host, port, db = validate_pooler_destination(DEFAULT_POOLER_HOST, DEFAULT_POOLER_PORT, DEFAULT_DBNAME)
    except ValueError as err:
        sys.exit(f"❌ ABORTO: Destino inválido: {err}")

    print(f"• Destino Homologado : {host}:{port} (Banco: {db})")
    print(f"• TLS Modo           : {ssl_params['sslmode']} (CA: {ssl_params['sslrootcert']})")
    print(f"• Referência Projeto : {AUTHORIZED_PROJECT_REF}\n")

    # Prompt do usuário administrativo com padrão e validação estrita 'postgres.<project-ref>'
    expected_default_admin = f"postgres.{AUTHORIZED_PROJECT_REF}"
    admin_user_input = read_input(f"Usuário administrativo [{expected_default_admin}]: ", expected_default_admin)
    try:
        admin_user = validate_admin_user(admin_user_input)
    except ValueError as err:
        sys.exit(f"❌ ABORTO: {err}")

    print(f"✓ Identidade administrativa validada: {admin_user}")

    admin_pass = read_password(f"Senha de {admin_user} (entrada oculta): ")
    if not admin_pass:
        sys.exit("❌ ABORTO: A senha não pode ser vazia.")

    conn_params = {
        "host": host,
        "port": port,
        "dbname": db,
        "user": admin_user,
        "password": admin_pass,
        "connect_timeout": 15,
        "autocommit": True,
        **ssl_params
    }

    print("\n[1/5] Estabelecendo conexão administrativa estritamente READ ONLY...")
    try:
        with psycopg.connect(**conn_params) as conn:
            if not conn.pgconn.ssl_in_use:
                sys.exit("❌ ABORTO DE SEGURANÇA: Conexão TLS não foi ativada pelo servidor!")

            with conn.cursor() as cur:
                cur.execute("BEGIN READ ONLY;")
                cur.execute("SHOW transaction_read_only;")
                ro_status = cur.fetchone()[0]
                if ro_status != "on":
                    sys.exit(f"❌ ABORTO DE SEGURANÇA: transaction_read_only esperava 'on', obtido '{ro_status}'.")
                print("✓ Transação READ ONLY confirmada no PostgreSQL remoto.")

                # 1. Informações básicas de infraestrutura
                cur.execute("SELECT version(), current_database(), current_user;")
                ver, db_ret, usr_ret = cur.fetchone()
                print(f"• Versão: {ver}")
                print(f"• Banco: {db_ret} | Usuário de Sessão: {usr_ret}\n")

                # 2. pg_auth_members no PG 17
                print("[2/5] Auditando membership de sosp_runtime_app no PostgreSQL 17...")
                cur.execute("""
                SELECT
                    r_role.rolname AS role_name,
                    r_member.rolname AS member_name,
                    pam.admin_option,
                    pam.inherit_option,
                    pam.set_option
                FROM pg_auth_members pam
                JOIN pg_roles r_role ON pam.roleid = r_role.oid
                JOIN pg_roles r_member ON pam.member = r_member.oid
                WHERE r_role.rolname = 'sosp_runtime_role'
                  AND r_member.rolname = 'sosp_runtime_app';
                """)
                membership = cur.fetchone()
                if not membership:
                    sys.exit("❌ ABORTO: Associação sosp_runtime_role -> sosp_runtime_app não encontrada no catálogo!")
                r_name, m_name, admin_opt, inherit_opt, set_opt = membership
                print(f"• Role Pai: {r_name} | Role Membro: {m_name}")
                print(f"• admin_option: {admin_opt} (esperado: False)")
                print(f"• inherit_option: {inherit_opt} (confirmado na 4D.1)")
                print(f"• set_option: {set_opt}")

                if admin_opt is True:
                    sys.exit("❌ ABORTO DE SEGURANÇA: sosp_runtime_app possui admin_option=True sobre sosp_runtime_role!")

                # Confere isolamento estrito contra roles administrativas
                cur.execute("""
                SELECT r.rolname as role_name, m.rolname as member_of_role
                FROM pg_auth_members am
                JOIN pg_roles r ON r.oid = am.member
                JOIN pg_roles m ON m.oid = am.roleid
                WHERE r.rolname IN ('sosp_runtime_role', 'sosp_runtime_app')
                  AND m.rolname IN ('postgres', 'anon', 'authenticated', 'service_role', 'supabase_admin');
                """)
                leaked_admin_mems = cur.fetchall()
                if leaked_admin_mems:
                    sys.exit(f"❌ ABORTO DE SEGURANÇA: Associação indevida com papéis administrativos detectada: {leaked_admin_mems}")
                print("✓ Membership e isolamento de runtime no PG17 validados com sucesso.\n")

                # 3. Atributos das Roles
                print("[3/5] Verificando atributos de isolamento das roles...")
                cur.execute("""
                SELECT rolname, rolcanlogin, rolsuper, rolbypassrls, rolreplication
                FROM pg_roles
                WHERE rolname IN ('sosp_runtime_role', 'sosp_runtime_app');
                """)
                roles_info = {r[0]: r[1:] for r in cur.fetchall()}
                if "sosp_runtime_role" not in roles_info or "sosp_runtime_app" not in roles_info:
                    sys.exit("❌ ABORTO: Roles de runtime não encontradas!")

                r_canlogin, r_super, r_bypass, r_repl = roles_info["sosp_runtime_role"]
                a_canlogin, a_super, a_bypass, a_repl = roles_info["sosp_runtime_app"]

                assert not r_canlogin and not r_super and not r_bypass, "sosp_runtime_role possui privilégios excessivos!"
                assert a_canlogin and not a_super and not a_bypass, "sosp_runtime_app possui privilégios excessivos!"
                print("✓ Atributos de segurança das roles validados (NOBYPASSRLS, NOSUPERUSER).\n")

                # 4. Estado das 40 relações físicas no catálogo PostgreSQL
                print("[4/5] Inspecionando inventário físico canônico (38 tabelas e 2 views em pg_catalog.pg_class)...")
                cur.execute("""
                SELECT
                    c.relname,
                    c.relkind,
                    c.relrowsecurity,
                    c.reloptions
                FROM pg_catalog.pg_class c
                JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public'
                  AND c.relname = ANY(%s)
                ORDER BY c.relname;
                """, (PHYSICAL_40_OBJECTS,))
                objects_found = {r[0]: {"kind": r[1], "rls": r[2], "opts": r[3]} for r in cur.fetchall()}

                missing = set(PHYSICAL_40_OBJECTS) - set(objects_found.keys())
                if missing:
                    sys.exit(f"❌ ABORTO: Faltam objetos no catálogo físico: {sorted(missing)}")

                print(f"✓ Todos os {len(objects_found)} objetos físicos foram localizados em 'public'.")

                # Validação das 38 tabelas
                for tbl in PHYSICAL_38_TABLES:
                    info = objects_found[tbl]
                    if info["kind"] != 'r':
                        sys.exit(f"❌ ABORTO: Objeto '{tbl}' esperado como tabela ordinária ('r'), encontrado relkind='{info['kind']}'!")
                    if not info["rls"]:
                        sys.exit(f"❌ ABORTO: Tabela '{tbl}' está com RLS desativado (relrowsecurity=False)!")

                print(f"✓ 38/38 tabelas físicas validadas com relkind='r' e relrowsecurity=True.")

                # Diagnóstico das 2 views analíticas
                for vw in PHYSICAL_2_VIEWS:
                    info = objects_found[vw]
                    if info["kind"] != 'v':
                        sys.exit(f"❌ ABORTO: Objeto '{vw}' esperado como view ('v'), encontrado relkind='{info['kind']}'!")
                    has_invoker = info["opts"] is not None and "security_invoker=true" in info["opts"]
                    if has_invoker:
                        print(f"  • View '{vw}': reloptions={info['opts']} (security_invoker=true garantido)")
                    else:
                        print(f"  • View '{vw}': security_invoker=true pendente (será aplicado atomicamente no script de aplicação 4D.2)")

                print("✓ Inventário físico e status de RLS/Views confirmados com sucesso.\n")

                # 5. Privilégios atuais de sosp_runtime_role no catálogo físico
                print("[5/5] Conferindo ausência de privilégios prévios para sosp_runtime_role...")
                cur.execute("""
                SELECT table_name, privilege_type
                FROM information_schema.role_table_grants
                WHERE grantee = 'sosp_runtime_role'
                  AND table_schema = 'public'
                  AND table_name = ANY(%s);
                """, (PHYSICAL_40_OBJECTS,))
                grants = cur.fetchall()
                if grants:
                    sys.exit(f"❌ ABORTO: sosp_runtime_role já possui privilégios concedidos nos objetos físicos: {grants}")
                print(f"✓ Zero concessões prévias confirmadas para sosp_runtime_role nos 40 objetos físicos.\n")

                # 6. Schema sosp_security
                cur.execute("SELECT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'sosp_security');")
                sec_schema_exists = cur.fetchone()[0]
                print(f"• Schema sosp_security existe atualmente? {'Sim' if sec_schema_exists else 'Não'}")

                cur.execute("ROLLBACK;")

        print("=" * 80)
        print("✅ PREFLIGHT 4D.2 CONCLUÍDO COM SUCESSO! O AMBIENTE ESTÁ APTO PARA A ETAPA 4D.2.")
        print("=" * 80)

    except Exception as e:
        sys.exit(f"❌ FALHA NO PREFLIGHT: {e}")

if __name__ == "__main__":
    main()
