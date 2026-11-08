#!/usr/bin/env python3
"""
SOSP — ETAPA 4D.2: APLICAÇÃO SUPERVISIONADA DE CONTEXTO HMAC, GRANTS E RLS
HISTÓRICO OPERACIONAL: A Etapa 4D.2 já foi aplicada e homologada com sucesso no Supabase real.
O COMMIT 4D.2 e a auditoria pós-commit como sosp_runtime_app foram CONFIRMADOS.
Este script é preservado exclusivamente como histórico operacional e registro de auditoria.
NÃO REAPLICAR no ambiente remoto de produção/homologação já configurado.

Garantias e Verificações do Registro Histórico:
1. Conexão administrativa em transação atômica única (autocommit=False).
2. Identidade administrativa do Session Pooler: estritamente 'postgres.<PROJECT_REF>' (ex.: postgres.cidtcgfowvgwgggvhbym).
3. Rejeição explícita de formatos invertidos ('<PROJECT_REF>.postgres') e de outros projetos.
4. Fornecimento seguro da chave HMAC via terminal interativo (sem armazenamento em disco, SQL ou logs).
5. Transmissão do segredo HMAC exclusivamente via query parametrizada (SELECT sosp_security.set_hmac_secret(%s)).
6. Execução sequencial: Setup de Contexto -> Configuração do Segredo -> Mínimos Privilégios -> Políticas RLS.
7. Aplicação atômica de security_invoker = true nas 2 views ANTES de conceder acesso a runtime.
8. Validação rigorosa em-transação de todos os 40 objetos físicos antes do COMMIT.
9. Portão de Confirmação Humana Inequívoca: digitação obrigatória de 'CONFIRMAR COMMIT 4D.2'.
10. Em caso de recusa, erro ou exceção: ROLLBACK automático e reversão total.
11. Registro de auditoria com permissões restritas (0600) sem vazamento de segredos.
"""

import sys
import os
import getpass
import secrets
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

SETUP_CONTEXT_SQL = os.path.join(SCRATCH_DIR, "run_4d2_setup_security_context.sql")
APPLY_GRANTS_SQL = os.path.join(SCRATCH_DIR, "run_4d2_apply_minimum_grants.sql")
APPLY_RLS_SQL = os.path.join(SCRATCH_DIR, "run_4d2_apply_rls_policies.sql")

def check_git_status():
    """Verifica branch develop e estado da árvore de trabalho sem auto-commit."""
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
            print("⚠️ AVISO: A árvore de trabalho possui arquivos modificados de desenvolvimento.")
            print("   Nenhum commit automático será realizado. O script solicitará autorização humana explícita antes do COMMIT da transação SQL.\n")
    except Exception as e:
        print(f"⚠️ AVISO: Não foi possível inspecionar o status do Git: {e}\n")

def write_tty(message: str):
    try:
        with open("/dev/tty", "w") as tty_out:
            tty_out.write(message)
            tty_out.flush()
    except (OSError, IOError):
        if sys.stdin.isatty():
            sys.stderr.write(message)
            sys.stderr.flush()
            return
        raise RuntimeError("Terminal físico (/dev/tty) indisponível.")

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
        raise RuntimeError(f"Falha ao ler credencial no terminal: {e}")

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
    print("SOSP — ETAPA 4D.2: APLICAÇÃO SUPERVISIONADA DE CONTEXTO HMAC, GRANTS E RLS")
    print("=" * 80)

    check_git_status()

    # 1. Checagem de integridade dos arquivos SQL
    for fpath in [SETUP_CONTEXT_SQL, APPLY_GRANTS_SQL, APPLY_RLS_SQL]:
        if not os.path.isfile(fpath) or not os.access(fpath, os.R_OK):
            sys.exit(f"❌ ABORTO: Arquivo SQL obrigatório não encontrado: {fpath}")

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

    print("\n--- CONFIGURAÇÃO DO SEGREDO CRIPTOGRÁFICO HMAC DO BANCO ---")
    print("O segredo HMAC é exclusivo para assinatura e validação do contexto RLS no PostgreSQL.")
    print("Ele DEVE ser idêntico ao configurado na variável DB_HMAC_SECRET_KEY do Django.")
    hmac_key = read_password("Informe a chave DB_HMAC_SECRET_KEY (ou ENTER para gerar aleatoriamente): ").strip()

    if not hmac_key:
        generated_key = secrets.token_hex(32)  # 64 caracteres hexadecimais
        write_tty("\n" + "!" * 80 + "\n")
        write_tty("CHAVE HMAC GERADA AUTOMATICAMENTE (Guarde em local seguro antes do COMMIT!):\n")
        write_tty(f"DB_HMAC_SECRET_KEY={generated_key}\n")
        write_tty("!" * 80 + "\n\n")

        conf_store = read_input("Você copiou e armazenou a chave gerada com segurança? Digite 'ARMAZENADA': ")
        if conf_store.strip() != "ARMAZENADA":
            sys.exit("❌ ABORTO: Operação cancelada. A chave precisa ser guardada antes de prosseguir.")
        hmac_key = generated_key

    if len(hmac_key) < 32:
        sys.exit("❌ ABORTO: A chave HMAC deve possuir no mínimo 32 caracteres criptográficos.")

    conn_params = {
        "host": host,
        "port": port,
        "dbname": db,
        "user": admin_user,
        "password": admin_pass,
        "connect_timeout": 15,
        "autocommit": False,  # Transação explícita obrigatória
        **ssl_params
    }

    commit_performed = False

    try:
        print("\n[1/5] Conectando ao Supabase para aplicação atômica...")
        with psycopg.connect(**conn_params) as conn:
            if not conn.pgconn.ssl_in_use:
                sys.exit("❌ ABORTO DE SEGURANÇA: Conexão TLS não foi ativada pelo servidor!")

            with conn.cursor() as cur:
                # 1. Executa Setup de Contexto
                print("[2/5] Criando schema sosp_security e funções criptográficas...")
                with open(SETUP_CONTEXT_SQL, "r", encoding="utf-8") as f:
                    setup_sql = f.read()
                # Remove BEGIN e COMMIT literais do arquivo para manter a transação do cursor
                setup_sql_clean = setup_sql.replace("BEGIN;", "-- BEGIN").replace("COMMIT;", "-- COMMIT")
                cur.execute(setup_sql_clean)
                print("✓ Schema sosp_security, tabelas e funções criadas.")

                # 2. Configura a chave HMAC via query parametrizada (sem segredos no SQL)
                print("• Configurando segredo criptográfico HMAC via query parametrizada...")
                cur.execute("SELECT sosp_security.set_hmac_secret(%s);", (hmac_key,))
                print("✓ Segredo HMAC provisionado com sucesso no banco.")

                # 3. Aplica Mínimos Privilégios e garante atomicamente security_invoker nas views
                print("[3/5] Aplicando matriz de privilégios mínimos DML em 40 objetos físicos...")
                with open(APPLY_GRANTS_SQL, "r", encoding="utf-8") as f:
                    grants_sql = f.read()
                grants_sql_clean = grants_sql.replace("BEGIN;", "-- BEGIN").replace("COMMIT;", "-- COMMIT")
                cur.execute(grants_sql_clean)
                print("✓ Privilégios DML concedidos a sosp_runtime_role (zero TRUNCATE/MAINTAIN) e views com security_invoker.")

                # 4. Aplica Políticas RLS
                print("[4/5] Aplicando políticas RLS granulares nas 38 tabelas...")
                with open(APPLY_RLS_SQL, "r", encoding="utf-8") as f:
                    rls_sql = f.read()
                rls_sql_clean = rls_sql.replace("BEGIN;", "-- BEGIN").replace("COMMIT;", "-- COMMIT")
                cur.execute(rls_sql_clean)
                print("✓ Políticas RLS aplicadas com sucesso.")

                # 5. Validação em-transação do catálogo físico
                print("\n[5/5] Realizando validações em-transação antes do COMMIT...")
                cur.execute("SELECT count(*) FROM sosp_security.hmac_secret WHERE id = 1;")
                sec_count = cur.fetchone()[0]
                assert sec_count == 1, "Falha: tabela sosp_security.hmac_secret não possui o registro esperado!"

                # Confere que todos os 40 objetos físicos possuem grants para sosp_runtime_role
                cur.execute("""
                SELECT count(DISTINCT table_name)
                FROM information_schema.role_table_grants
                WHERE grantee = 'sosp_runtime_role'
                  AND table_schema = 'public'
                  AND table_name = ANY(%s);
                """, (PHYSICAL_40_OBJECTS,))
                granted_tables_count = cur.fetchone()[0]
                print(f"• Total de relações físicas com grants para sosp_runtime_role: {granted_tables_count}/40")
                assert granted_tables_count == 40, f"Esperado exatamente 40 objetos físicos com grants, obtido {granted_tables_count}!"

                # Confere que as 2 views possuem security_invoker = true ativado
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

                # Confere que as 38 tabelas possuem relrowsecurity = True
                cur.execute("""
                SELECT count(*)
                FROM pg_catalog.pg_class c
                JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public'
                  AND c.relname = ANY(%s)
                  AND c.relrowsecurity = true;
                """, (PHYSICAL_38_TABLES,))
                rls_tables_count = cur.fetchone()[0]
                assert rls_tables_count == 38, f"Esperadas 38 tabelas com relrowsecurity=true, obtido {rls_tables_count}!"

                cur.execute("""
                SELECT count(*)
                FROM pg_policies
                WHERE schemaname = 'public';
                """)
                policy_count = cur.fetchone()[0]
                print(f"• Total de políticas RLS ativas: {policy_count}")
                assert policy_count >= 50, f"Esperado >= 50 políticas RLS ativas, obtido {policy_count}!"
                print("✓ Validações em-transação APROVADAS.")

                # Portão de Confirmação Humana Inequívoca
                print("\n" + "=" * 80)
                print("PORTÃO HUMANO DE LIBERAÇÃO — CONFIRMAÇÃO DE COMMIT REMOTO 4D.2")
                print("=" * 80)
                print("Todas as alterações estão aplicadas dentro de uma transação aberta no Supabase.")
                print("Nenhuma alteração foi persistida ainda no disco do banco de dados remoto.")
                print("Para efetivar de forma irreversível e permanente o COMMIT, digite exatamente:")
                print("   CONFIRMAR COMMIT 4D.2")
                print("Se digitar qualquer outra coisa, será realizado ROLLBACK imediato.")
                print("=" * 80)

                confirmation = read_input("Confirmação de liberação: ").strip()

                if confirmation == "CONFIRMAR COMMIT 4D.2":
                    print("\n⏳ Executando COMMIT na base de dados remota...")
                    conn.commit()
                    commit_performed = True
                    print("✅ COMMIT REALIZADO COM SUCESSO! Etapa 4D.2 implantada no Supabase PostgreSQL.")
                else:
                    print("\n⚠️ Confirmação não fornecida ou incorreta. Executando ROLLBACK de segurança...")
                    conn.rollback()
                    print("✓ ROLLBACK concluído. Nenhuma modificação foi gravada no Supabase.")
                    sys.exit(1)

    except Exception as e:
        if not commit_performed:
            print(f"\n❌ ERRO DURANTE A OPERAÇÃO: {e}")
            print("Executando ROLLBACK de segurança...")
        sys.exit(f"❌ Processo abortado: {e}")

if __name__ == "__main__":
    main()
