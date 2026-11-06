#!/usr/bin/env python3
"""
SOSP — Script de Pré-Voo: Inspeção de Schema Somente Leitura (Etapa 4A)

Objetivo:
Inspeciona schemas, tabelas, migrações registradas, extensões instaladas,
roles e políticas de RLS antes de qualquer execução de DDL no Supabase.

Garantias de Segurança:
- Conexão configurada com 'default_transaction_read_only=on' (rejeita qualquer escrita a nível de motor).
- Não executa comandos DDL, INSERT, UPDATE, DELETE ou migrações.
- Não expõe senhas ou tokens sensíveis.
- Retorna resumo diagnóstico estruturado.
"""

import os
import sys
import argparse
from typing import Dict, Any, List, Set

SOSP_EXPECTED_TABLES: Set[str] = {
    "accountsgender",
    "accountscitizen",
    "accountsinternaluser",
    "accountssession",
    "accountsloginattempt",
    "accountspasswordreset",
    "catalogagency",
    "catalogunit",
    "catalogunitopeninghour",
    "catalognonworkingday",
    "catalogservice",
    "catalogserviceagency",
    "catalogunitservice",
    "catalogservicestep",
    "catalogservicedocument",
    "catalogfaq",
    "catalogserviceversion",
    "searchquerylog",
    "searchsynonym",
    "guidanceprogress",
    "guidancegeneratedpdf",
    "schedulingslot",
    "schedulingappointment",
    "schedulingprotocol",
    "schedulingprotocolattachment",
    "schedulingprotocoltransition",
    "feedbackreview",
    "feedbackreviewreport",
    "feedbackquestion",
    "notificationstemplate",
    "notificationspreference",
    "notificationsdelivery",
    "notificationspushsubscription",
    "reportsexport",
    "auditevent",
    "auditdatasubjectrequest",
}

SOSP_EXPECTED_VIEWS: Set[str] = {
    "vw_catalogservicesearch",
    "vw_schedulingslotavailability",
}


def mask_string(val: str, show_chars: int = 4) -> str:
    if not val:
        return "[NÃO DEFINIDO]"
    if len(val) <= show_chars * 2:
        return "***"
    return f"{val[:show_chars]}...{val[-show_chars:]}"


def inspect_database(conn_info: Dict[str, Any]) -> int:
    try:
        import psycopg
    except ImportError:
        print("✗ Erro: Biblioteca 'psycopg' não encontrada.")
        return 1

    # Força transação em modo estritamente somente-leitura na conexão
    conn_info["options"] = "-c default_transaction_read_only=on"

    try:
        with psycopg.connect(**conn_info) as conn:
            with conn.cursor() as cur:
                print("✓ Conexão estabelecida em modo SOMENTE LEITURA (default_transaction_read_only=on).\n")

                # 1. Informações da Instância e Sessão
                cur.execute("SELECT current_database(), current_user, session_user, version();")
                db_name, cur_user, sess_user, version_str = cur.fetchone()
                print("1. AMBIENTE E SESSÃO ATIVA")
                print(f"   - Banco:    {db_name}")
                print(f"   - Usuário:  {cur_user} (Session: {sess_user})")
                print(f"   - Versão:   {version_str.split(',')[0]}")

                # 2. Privilégios do Usuário Conectado
                print("\n2. PRIVILÉGIOS DA ROLE ATIVA")
                cur.execute(
                    """
                    SELECT rolname, rolsuper, rolcreaterole, rolcreatedb, rolcanlogin, rolinherit
                    FROM pg_roles WHERE rolname = current_user;
                    """
                )
                role_info = cur.fetchone()
                if role_info:
                    print(f"   - Superusuário:  {'SIM' if role_info[1] else 'Não'}")
                    print(f"   - Pode criar BD: {'SIM' if role_info[3] else 'Não'}")
                    print(f"   - Pode logar:    {'SIM' if role_info[4] else 'Não'}")
                cur.execute("SELECT has_schema_privilege(current_user, 'public', 'CREATE');")
                can_create_in_public = cur.fetchone()[0]
                print(f"   - Permissão CREATE no schema 'public': {'SIM (Pode rodar migrations)' if can_create_in_public else 'NÃO (Sem permissão DDL)'}")

                # 3. Extensões Instaladas
                print("\n3. EXTENSÕES POSTGRESQL INSTALADAS")
                cur.execute("SELECT extname, extversion FROM pg_extension ORDER BY extname;")
                installed_extensions = dict(cur.fetchall())
                for ext, ver in installed_extensions.items():
                    print(f"   - {ext:<15} (versão {ver})")
                
                missing_exts = []
                for req_ext in ("unaccent", "pg_trgm"):
                    if req_ext not in installed_extensions:
                        missing_exts.append(req_ext)
                if missing_exts:
                    print(f"   ⚠️  Extensões recomendadas ausentes: {', '.join(missing_exts)} (serão criadas pelo baseline se houver privilégio)")
                else:
                    print("   ✓ Extensões essenciais 'unaccent' e 'pg_trgm' já estão ativas.")

                # 4. Tabelas Existentes no Schema 'public'
                print("\n4. TABELAS NO SCHEMA 'public'")
                cur.execute(
                    """
                    SELECT tablename
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    ORDER BY tablename;
                    """
                )
                existing_tables = [r[0].lower() for r in cur.fetchall()]
                print(f"   - Total de tabelas encontradas em 'public': {len(existing_tables)}")

                sosp_present = set(existing_tables).intersection(SOSP_EXPECTED_TABLES)
                sosp_missing = SOSP_EXPECTED_TABLES - set(existing_tables)

                print(f"   - Tabelas de domínio SOSP presentes: {len(sosp_present)} de {len(SOSP_EXPECTED_TABLES)}")

                # 5. Views Existentes no Schema 'public'
                print("\n5. VIEWS NO SCHEMA 'public'")
                cur.execute(
                    """
                    SELECT viewname
                    FROM pg_views
                    WHERE schemaname = 'public'
                    ORDER BY viewname;
                    """
                )
                existing_views = [r[0].lower() for r in cur.fetchall()]
                for v in existing_views:
                    print(f"   - View: {v}")

                # 6. Histórico de Migrations do Django
                print("\n6. HISTÓRICO DE MIGRATIONS (django_migrations)")
                if "django_migrations" in existing_tables:
                    cur.execute("SELECT app, name, applied FROM django_migrations ORDER BY applied;")
                    migrations = cur.fetchall()
                    print(f"   - Total de migrations aplicadas: {len(migrations)}")
                    for app, name, applied in migrations:
                        print(f"     * {app:<15} {name:<25} ({applied.strftime('%Y-%m-%d %H:%M:%S')})")
                else:
                    print("   - Tabela 'django_migrations' não existe no banco (Banco inicial limpo).")

                # 7. Diagnóstico de RLS (Row Level Security)
                print("\n7. STATUS DE RLS NAS TABELAS DO SOSP")
                cur.execute(
                    """
                    SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity
                    FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE n.nspname = 'public' AND c.relkind = 'r'
                    ORDER BY c.relname;
                    """
                )
                rls_rows = cur.fetchall()
                tables_with_rls = [r[0] for r in rls_rows if r[1]]
                print(f"   - Tabelas com RLS habilitado: {len(tables_with_rls)} de {len(rls_rows)}")

                # 8. SÍNTESE DO ESTADO DIAGNÓSTICO
                print("\n" + "=" * 70)
                print("SÍNTESE DIAGNÓSTICA PARA EXECUÇÃO FUTURA DE MIGRATIONS")
                print("=" * 70)
                if len(sosp_present) == 0 and "django_migrations" not in existing_tables:
                    print("🟢 STATUS: PRONTO PARA IMPLANTAÇÃO INICIAL (READY_FOR_BASELINE)")
                    print("   O schema 'public' está limpo de tabelas da aplicação.")
                    print("   A migration 'accounts.0001_initial' poderá ser aplicada normalmente quando autorizada.")
                elif len(sosp_present) == len(SOSP_EXPECTED_TABLES):
                    print("🔵 STATUS: BASE TOTALMENTE IMPLANTADA (ALREADY_PROVISIONED)")
                    print("   Todas as 36 tabelas de aplicação já existem no PostgreSQL.")
                else:
                    print("🟡 STATUS: ESTADO PARCIAL / DIVERGENTE DETECTADO (PARTIAL_STATE)")
                    print(f"   Existem {len(sosp_present)} tabelas do SOSP criadas e {len(sosp_missing)} ausentes.")
                    print("   Atenção: Requer investigação detalhada antes de rodar migrations para evitar conflito.")

                return 0

    except psycopg.OperationalError as e:
        err_msg = str(e)
        if conn_info.get("password") and conn_info["password"] in err_msg:
            err_msg = err_msg.replace(conn_info["password"], "[SENHA MASCARADA]")
        print(f"✗ Erro de conexão durante inspeção: {err_msg}")
        return 1
    except Exception as e:
        print(f"✗ Erro inesperado: {type(e).__name__}: {e}")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="SOSP Preflight Schema Inspection (Somente Leitura / Não destrutivo)"
    )
    parser.add_argument("--host", default=os.environ.get("DB_HOST", "localhost"), help="Host do banco")
    parser.add_argument("--port", type=int, default=int(os.environ.get("DB_PORT", "5432")), help="Porta do banco")
    parser.add_argument("--dbname", default=os.environ.get("DB_NAME", "postgres"), help="Nome da base")
    parser.add_argument("--user", default=os.environ.get("DB_USER", "postgres"), help="Usuário")
    parser.add_argument("--password", default=os.environ.get("DB_PASSWORD", ""), help="Senha")
    parser.add_argument("--sslmode", default=os.environ.get("DB_SSLMODE", "prefer"), help="Modo SSL")

    args = parser.parse_args()

    conn_info = {
        "host": args.host,
        "port": args.port,
        "dbname": args.dbname,
        "user": args.user,
        "password": args.password,
        "sslmode": args.sslmode,
        "connect_timeout": 8,
    }

    print("=" * 70)
    print("SOSP — Pré-Voo: Inspeção de Schemas e Tabelas (Somente Leitura)")
    print("=" * 70)
    print(f"Host:     {mask_string(args.host)}")
    print(f"Porta:    {args.port}")
    print(f"Base:     {args.dbname}")
    print(f"Usuário:  {mask_string(args.user)}")
    print(f"SSL Mode: {args.sslmode}")
    print("-" * 70)

    exit_code = inspect_database(conn_info)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
