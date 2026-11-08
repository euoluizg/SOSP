#!/usr/bin/env python3
"""
SOSP — ETAPA 4D.2: ROLLBACK REMOTO SUPERVISIONADO (PORTÃO E)
Execução: Terminal interativo do proprietário (@euoluizg).
Garantias e Verificações Obrigatórias:
1. Conexão administrativa em transação atômica única (autocommit=False).
2. Identidade administrativa do Session Pooler: estritamente 'postgres.<PROJECT_REF>' (ex.: postgres.cidtcgfowvgwgggvhbym).
3. Rejeição explícita de formatos invertidos ('<PROJECT_REF>.postgres') e de outros projetos.
4. Execução cirúrgica objeto a objeto sem uso de CASCADE:
   - run_4d2_rollback_rls_policies.sql (DROP das políticas, funções, tabelas e schema sosp_security com RESTRICT)
   - run_4d2_rollback_minimum_grants.sql (REVOKE de todos os privilégios DML de sosp_runtime_role)
5. Validação em-transação do retorno ao estado exato pós-4D.1 contra o catálogo físico (40 objetos).
6. Portão de Confirmação Humana Inequívoca: digitação obrigatória de 'CONFIRMAR ROLLBACK 4D.2'.
7. Em caso de recusa: cancelamento com rollback imediato.
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
    PHYSICAL_40_OBJECTS,
    validate_admin_user,
    validate_pooler_destination,
    validate_tls_params,
)

ROLLBACK_RLS_SQL = os.path.join(SCRATCH_DIR, "run_4d2_rollback_rls_policies.sql")
ROLLBACK_GRANTS_SQL = os.path.join(SCRATCH_DIR, "run_4d2_rollback_minimum_grants.sql")

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
            print("   Nenhum commit automático será realizado. O rollback solicitará confirmação humana explícita.\n")
    except Exception as e:
        print(f"⚠️ AVISO: Não foi possível inspecionar o status do Git: {e}\n")

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
    print("SOSP — ETAPA 4D.2: ROLLBACK REMOTO SUPERVISIONADO (PORTÃO E)")
    print("=" * 80)

    check_git_status()

    for fpath in [ROLLBACK_RLS_SQL, ROLLBACK_GRANTS_SQL]:
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
    print(f"• Operação           : Reversão integral e cirúrgica da Etapa 4D.2\n")

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
        sys.exit("❌ ABORTO: Senha não pode ser vazia.")

    conn_params = {
        "host": host,
        "port": port,
        "dbname": db,
        "user": admin_user,
        "password": admin_pass,
        "connect_timeout": 15,
        "autocommit": False,
        **ssl_params
    }

    try:
        print("\n[1/4] Conectando ao banco em transação de rollback atômica...")
        with psycopg.connect(**conn_params) as conn:
            if not conn.pgconn.ssl_in_use:
                sys.exit("❌ ABORTO DE SEGURANÇA: Conexão TLS não foi ativada!")

            with conn.cursor() as cur:
                print("[2/4] Executando remoção cirúrgica de políticas RLS e schema sosp_security...")
                with open(ROLLBACK_RLS_SQL, "r", encoding="utf-8") as f:
                    rls_rb_sql = f.read().replace("BEGIN;", "-- BEGIN").replace("COMMIT;", "-- COMMIT")
                cur.execute(rls_rb_sql)
                print("✓ Políticas RLS, funções e schema sosp_security removidos.")

                print("[3/4] Revogando privilégios DML de sosp_runtime_role...")
                with open(ROLLBACK_GRANTS_SQL, "r", encoding="utf-8") as f:
                    grants_rb_sql = f.read().replace("BEGIN;", "-- BEGIN").replace("COMMIT;", "-- COMMIT")
                cur.execute(grants_rb_sql)
                print("✓ Privilégios DML revogados.")

                # Validação em-transação contra o catálogo físico
                print("\n[4/4] Validando retorno ao estado pós-4D.1 contra o catálogo físico...")
                cur.execute("SELECT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'sosp_security');")
                sec_exists = cur.fetchone()[0]
                assert not sec_exists, "Falha: schema sosp_security ainda existe!"

                cur.execute("""
                SELECT count(*) FROM information_schema.role_table_grants
                WHERE grantee = 'sosp_runtime_role'
                  AND table_schema = 'public'
                  AND table_name = ANY(%s);
                """, (PHYSICAL_40_OBJECTS,))
                grants_rem = cur.fetchone()[0]
                assert grants_rem == 0, f"Falha: ainda restam {grants_rem} grants para sosp_runtime_role nos 40 objetos físicos!"

                print("✓ Validação em-transação de rollback aprovada nos 40 objetos físicos.")

                print("\n" + "=" * 80)
                print("CONFIRMAÇÃO FINAL DE ROLLBACK 4D.2")
                print("=" * 80)
                print("Para confirmar a reversão e retornar ao estado pós-4D.1, digite exatamente:")
                print("   CONFIRMAR ROLLBACK 4D.2")
                print("Qualquer outro valor cancelará o rollback e manterá o banco como está.")
                print("=" * 80)

                conf = read_input("Confirmação: ").strip()
                if conf == "CONFIRMAR ROLLBACK 4D.2":
                    conn.commit()
                    print("\n✅ ROLLBACK 4D.2 CONCLUÍDO COM SUCESSO! Banco restaurado ao estado pós-4D.1.")
                else:
                    conn.rollback()
                    print("\n⚠️ Rollback cancelado pelo operador. Nenhuma alteração foi persistida.")

    except Exception as e:
        sys.exit(f"❌ FALHA NO ROLLBACK: {e}")

if __name__ == "__main__":
    main()
