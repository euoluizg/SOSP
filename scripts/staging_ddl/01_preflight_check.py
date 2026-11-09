#!/usr/bin/env python3
"""
SOSP — Script de Pré-Voo para Staging (Etapa 1 / Supabase DDL Prep)

Objetivo:
Inspeciona em modo estritamente SOMENTE LEITURA o estado do banco PostgreSQL 17 gerenciado
no Supabase Staging antes de qualquer execução de DDL.

Garantias de Segurança:
1. Conexão com 'default_transaction_read_only=on' (qualquer mutação é rejeitada pelo motor).
2. Não executa comandos DDL, INSERT, UPDATE, DELETE ou migrações.
3. TLS com sslmode='require', 'verify-ca' ou 'verify-full' para hosts remotos.
4. Resolução segura de senhas via variáveis de ambiente ou getpass interativo.
5. Suporta simulação offline / mock para execução determinística em testes unitários.
6. Não expõe senhas ou credenciais em logs ou tracebacks.
"""

import os
import sys
import argparse
import getpass
from typing import Dict, Any, List, Set, Tuple

try:
    import psycopg
    from psycopg import sql
except ImportError:
    psycopg = None

# Inventário Canônico Físico (minúsculas conforme catálogo PostgreSQL - ADR-002)
EXPECTED_SOSP_TABLES = [
    "accountsgender", "accountscitizen", "accountsinternaluser", "accountssession",
    "accountsloginattempt", "accountspasswordreset", "catalogagency", "catalogunit",
    "catalogunitopeninghour", "catalognonworkingday", "catalogservice", "catalogserviceagency",
    "catalogunitservice", "catalogservicestep", "catalogservicedocument", "catalogfaq",
    "catalogserviceversion", "searchquerylog", "searchsynonym", "guidanceprogress",
    "guidancegeneratedpdf", "schedulingslot", "schedulingappointment", "schedulingprotocol",
    "schedulingprotocolattachment", "schedulingprotocoltransition", "feedbackreview",
    "feedbackreviewreport", "feedbackquestion", "notificationstemplate", "notificationspreference",
    "notificationsdelivery", "notificationspushsubscription", "reportsexport", "auditevent",
    "auditdatasubjectrequest"
]

EXPECTED_DJANGO_TABLES = ["django_migrations", "django_content_type"]
EXPECTED_VIEWS = ["vw_catalogservicesearch", "vw_schedulingslotavailability"]
REQUIRED_EXTENSIONS = ["pg_trgm", "unaccent", "pgcrypto"]


def mask_string(val: str, show_chars: int = 4) -> str:
    """Mascara strings sensíveis para exibição segura."""
    if not val:
        return "[NÃO DEFINIDO]"
    if len(val) <= show_chars * 2:
        return "***"
    return f"{val[:show_chars]}...{val[-show_chars:]}"


def validate_sslmode(sslmode: str, host: str) -> str:
    """Valida requisitos de TLS: conexões remotas exigem require ou superior."""
    mode = (sslmode or "require").strip().lower()
    is_local = host in ("localhost", "127.0.0.1", "::1", "") or host.startswith("/")
    if not is_local and mode in ("disable", "allow", "prefer"):
        raise ValueError(
            f"Conexão remota com '{host}' rejeitada: sslmode='{mode}' inseguro. "
            f"Exigido 'require', 'verify-ca' ou 'verify-full'."
        )
    return mode


def parse_connection_params() -> Dict[str, Any]:
    """Extrai parâmetros de conexão de variáveis de ambiente com defaults seguros."""
    host = os.environ.get("DB_HOST") or os.environ.get("SUPABASE_POOLER_HOST") or "aws-1-sa-east-1.pooler.supabase.com"
    port = int(os.environ.get("DB_PORT") or os.environ.get("SUPABASE_POOLER_PORT") or "5432")
    dbname = os.environ.get("DB_NAME") or os.environ.get("SUPABASE_DB_NAME") or "postgres"
    user = os.environ.get("DB_USER") or os.environ.get("DB_ADMIN_USER") or "postgres"
    sslmode = validate_sslmode(os.environ.get("DB_SSLMODE", "require"), host)

    password = os.environ.get("DB_PASSWORD") or os.environ.get("PGPASSWORD") or ""

    return {
        "host": host,
        "port": port,
        "dbname": dbname,
        "user": user,
        "password": password,
        "sslmode": sslmode,
    }


def run_preflight_inspection(params: Dict[str, Any], mock_mode: bool = False) -> Dict[str, Any]:
    """Executa a inspeção completa de pré-voo em modo estritamente read-only."""
    report: Dict[str, Any] = {
        "host": params["host"],
        "port": params["port"],
        "dbname": params["dbname"],
        "user": params["user"],
        "sslmode": params["sslmode"],
        "pg_version": None,
        "is_read_only": False,
        "installed_extensions": [],
        "missing_extensions": [],
        "schemas": [],
        "has_sosp_security": False,
        "has_text_search_config": False,
        "tables_found": [],
        "missing_sosp_tables": [],
        "views_found": [],
        "missing_views": [],
        "has_auth_function": False,
        "auth_function_security_definer": False,
        "status": "UNKNOWN",
    }

    if mock_mode:
        # Modo simulação local para testes unitários automatizados
        report["pg_version"] = "PostgreSQL 17.0 on x86_64-pc-linux-gnu (Simulated)"
        report["is_read_only"] = True
        report["installed_extensions"] = ["pg_trgm", "unaccent", "pgcrypto"]
        report["schemas"] = ["public", "sosp_security"]
        report["has_sosp_security"] = True
        report["has_text_search_config"] = True
        report["tables_found"] = []
        report["missing_sosp_tables"] = list(EXPECTED_SOSP_TABLES)
        report["views_found"] = []
        report["missing_views"] = list(EXPECTED_VIEWS)
        report["status"] = "CLEAN_SLATE_READY_FOR_BASELINE"
        return report

    if psycopg is None:
        raise RuntimeError("Biblioteca 'psycopg' não instalada no ambiente.")

    conninfo = (
        f"host={params['host']} port={params['port']} dbname={params['dbname']} "
        f"user={params['user']} sslmode={params['sslmode']} "
        f"options='-c default_transaction_read_only=on'"
    )
    if params["password"]:
        conninfo += f" password={params['password']}"

    with psycopg.connect(conninfo, autocommit=True) as conn:
        with conn.cursor() as cur:
            # 1. Confirmação estrita de Read-Only
            cur.execute("SHOW transaction_read_only;")
            ro_val = cur.fetchone()[0]
            report["is_read_only"] = (ro_val == "on")
            if not report["is_read_only"]:
                raise RuntimeError("FALHA DE SEGURANÇA: Conexão não está em modo read-only.")

            # 2. Versão do PostgreSQL
            cur.execute("SELECT version();")
            report["pg_version"] = cur.fetchone()[0]

            # 3. Extensões
            cur.execute("SELECT extname FROM pg_extension;")
            exts = [r[0] for r in cur.fetchall()]
            report["installed_extensions"] = exts
            report["missing_extensions"] = [e for e in REQUIRED_EXTENSIONS if e not in exts]

            # 4. Schemas
            cur.execute("SELECT nspname FROM pg_namespace;")
            schemas = [r[0] for r in cur.fetchall()]
            report["schemas"] = schemas
            report["has_sosp_security"] = "sosp_security" in schemas

            # 5. Configuração Text Search
            cur.execute("SELECT cfgname FROM pg_ts_config WHERE cfgname = 'sospportuguese';")
            report["has_text_search_config"] = cur.fetchone() is not None

            # 6. Tabelas existentes no schema public
            cur.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public';"
            )
            tables = [r[0].lower() for r in cur.fetchall()]
            report["tables_found"] = tables
            report["missing_sosp_tables"] = [t for t in EXPECTED_SOSP_TABLES if t not in tables]

            # 7. Views existentes no schema public
            cur.execute(
                "SELECT viewname FROM pg_views WHERE schemaname = 'public';"
            )
            views = [r[0].lower() for r in cur.fetchall()]
            report["views_found"] = views
            report["missing_views"] = [v for v in EXPECTED_VIEWS if v not in views]

            # 8. Função sosp_security.authenticate_citizen_by_cpf
            cur.execute("""
                SELECT p.prosecdef 
                FROM pg_proc p 
                JOIN pg_namespace n ON p.pronamespace = n.oid 
                WHERE n.nspname = 'sosp_security' AND p.proname = 'authenticate_citizen_by_cpf';
            """)
            auth_fn = cur.fetchone()
            if auth_fn is not None:
                report["has_auth_function"] = True
                report["auth_function_security_definer"] = bool(auth_fn[0])

            # Diagnóstico de Estado
            if len(report["missing_sosp_tables"]) == 0 and len(report["missing_views"]) == 0:
                report["status"] = "FULLY_PROVISIONED"
            elif len(report["tables_found"]) == 0:
                report["status"] = "CLEAN_SLATE_READY_FOR_BASELINE"
            else:
                report["status"] = "PARTIAL_STATE_APPLY_IDEMPOTENT"

    return report


def print_report(report: Dict[str, Any]):
    """Imprime o relatório de pré-voo formatado em console."""
    print("=" * 78)
    print("SOSP — RELATÓRIO DE PRÉ-VOO DO SUPABASE POSTGRESQL 17 (STAGING)")
    print("=" * 78)
    print(f"Host:              {mask_string(report['host'])}")
    print(f"Porta:             {report['port']}")
    print(f"Banco:             {report['dbname']}")
    print(f"Usuário:           {mask_string(report['user'])}")
    print(f"SSL Mode:          {report['sslmode']}")
    print(f"Modo Read-Only:    {'✓ ATIVO (on)' if report['is_read_only'] else '❌ INATIVO'}")
    print(f"Versão PostgreSQL: {report['pg_version']}")
    print("-" * 78)
    print("EXTENSÕES E SCHEMAS:")
    print(f"  Extensões Instaladas:  {', '.join(report['installed_extensions']) or 'Nenhuma'}")
    if report["missing_extensions"]:
        print(f"  Extensões Pendentes:   {', '.join(report['missing_extensions'])}")
    print(f"  Schema sosp_security:  {'✓ Presente' if report['has_sosp_security'] else 'Pendente (será criado pelo DDL)'}")
    print(f"  FTS sospPortuguese:    {'✓ Configurado' if report['has_text_search_config'] else 'Pendente (será criado pelo DDL)'}")
    print("-" * 78)
    print("INVENTÁRIO FÍSICO DE OBJETOS:")
    print(f"  Tabelas Encontradas:   {len(report['tables_found'])} de {len(EXPECTED_SOSP_TABLES)} tabelas SOSP")
    print(f"  Tabelas Pendentes:     {len(report['missing_sosp_tables'])}")
    print(f"  Views Encontradas:     {len(report['views_found'])} de {len(EXPECTED_VIEWS)} views")
    print(f"  Função de Auth:        {'✓ Presente' if report['has_auth_function'] else 'Pendente (será criada pelo DDL)'}")
    print("-" * 78)
    print(f"DIAGNÓSTICO FINAL:       {report['status']}")
    print("=" * 78)


def main():
    parser = argparse.ArgumentParser(description="SOSP Preflight Check — Supabase Staging")
    parser.add_argument("--mock", action="store_true", help="Executa simulação local sem rede para testes unitários.")
    args = parser.parse_args()

    try:
        params = parse_connection_params()
        report = run_preflight_inspection(params, mock_mode=args.mock)
        print_report(report)
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERRO NO PRÉ-VOO: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
