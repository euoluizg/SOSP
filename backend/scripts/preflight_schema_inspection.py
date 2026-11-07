#!/usr/bin/env python3
"""
SOSP — Script de Pré-Voo: Inspeção de Schema Somente Leitura (Etapa 4A / Hardened)

Objetivo:
Inspeciona schemas, tabelas, views, migrações registradas, extensões instaladas,
roles, privilégios DDL e políticas de RLS antes de qualquer execução de DDL no Supabase.

Garantias de Segurança:
- Conexão configurada com 'default_transaction_read_only=on' (rejeita qualquer escrita a nível de motor).
- Não executa comandos DDL, INSERT, UPDATE, DELETE ou migrações.
- Não expõe senhas ou tokens sensíveis em logs ou tracebacks.
- Exige sslmode='require', 'verify-ca' ou 'verify-full' para hosts remotos (sem fallback para prefer/disable).
- Preserva compatibilidade com bancos locais (sslmode prefer/disable aceitos em localhost/socket).
- Lê credenciais exclusivamente de variáveis de ambiente ou getpass interativo (passagem de senha por flag de linha de comando desabilitada).
- Avaliação estrita: não confunde 'nenhuma tabela SOSP' com 'banco limpo'.
- Esclarece que READY_FOR_BASELINE é uma avaliação preliminar, não uma autorização automática para migrations.
- Retorna código:
  * 0: READY_FOR_BASELINE ou ALREADY_PROVISIONED
  * 1: Erro de conexão, autenticação, SSL ou biblioteca
  * 2: PARTIAL_STATE ou MANUAL_REVIEW_REQUIRED (requer intervenção)
"""

import os
import sys
import argparse
import getpass
from typing import Dict, Any, List, Set, Tuple

VALID_SSLMODES = ("disable", "allow", "prefer", "require", "verify-ca", "verify-full")
RESTRICTIVE_REMOTE_SSLMODES = ("require", "verify-ca", "verify-full")

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

DJANGO_CORE_TABLES: Set[str] = {
    "django_migrations",
    "django_content_type",
}

EXPECTED_BASELINE_MIGRATIONS: List[Tuple[str, str]] = [
    ("accounts", "0001_initial"),
    ("catalog", "0001_initial"),
    ("catalog", "0002_align_orm_state_with_schema"),
    ("search", "0001_initial"),
    ("search", "0002_align_orm_state_with_schema"),
    ("guidance", "0001_initial"),
    ("guidance", "0002_align_orm_state_with_schema"),
    ("scheduling", "0001_initial"),
    ("feedback", "0001_initial"),
    ("notifications", "0001_initial"),
    ("reports", "0001_initial"),
    ("audit", "0001_initial"),
    ("contenttypes", "0001_initial"),
    ("contenttypes", "0002_remove_content_type_name"),
]


def mask_string(val: str, show_chars: int = 4) -> str:
    """Mascara strings sensíveis preservando prefixo identificador."""
    if not val:
        return "[NÃO DEFINIDO]"
    if len(val) <= show_chars * 2:
        return "***"
    return f"{val[:show_chars]}...{val[-show_chars:]}"


def validate_sslmode(sslmode: str, host: str) -> str:
    """
    Valida e normaliza o sslmode garantindo segurança de transporte.
    Para hosts remotos, exige 'require', 'verify-ca' ou 'verify-full'.
    Proíbe 'disable', 'allow' ou 'prefer' em conexões remotas.
    Preserva compatibilidade com bancos locais (localhost, socket Unix).
    """
    normalized = sslmode.strip().lower()
    if normalized not in VALID_SSLMODES:
        raise ValueError(
            f"sslmode inválido: '{sslmode}'. Valores válidos: {', '.join(VALID_SSLMODES)}."
        )

    is_remote = host not in ("localhost", "127.0.0.1", "") and not host.startswith("/")
    if is_remote and normalized not in RESTRICTIVE_REMOTE_SSLMODES:
        raise ValueError(
            f"Conexão remota rejeitada por governança de segurança: sslmode='{sslmode}' é proibido para o host remoto '{mask_string(host)}'. "
            f"Para conexões remotas (como Supabase), sslmode deve ser 'require', 'verify-ca' ou 'verify-full'. "
            "Fallback para SSL desabilitado ou prefer é terminantemente proibido."
        )
    return normalized


def resolve_password(host: str = "localhost") -> str:
    """
    Resolve a senha de forma segura exclusivamente via variáveis de ambiente
    (DB_PASSWORD / PGPASSWORD) ou entrada interativa oculta via getpass.
    A passagem de senhas via linha de comando (CLI) foi removida por segurança.
    """
    env_pwd = os.environ.get("DB_PASSWORD") or os.environ.get("PGPASSWORD")
    if env_pwd:
        return env_pwd
    is_remote = host not in ("localhost", "127.0.0.1", "") and not host.startswith("/")
    if not is_remote:
        # Para hosts locais (localhost, socket Unix), não solicita senha por padrão (autenticação trust/peer)
        return ""
    if sys.stdin.isatty():
        try:
            return getpass.getpass("Digite a senha do PostgreSQL (ou Enter para vazio): ")
        except (EOFError, KeyboardInterrupt):
            print("\nOperação cancelada pelo usuário.")
            sys.exit(1)
    if is_remote:
        print("  ⚠️  Aviso: Nenhuma senha fornecida para conexão remota (defina DB_PASSWORD ou PGPASSWORD).")
    return ""


def evaluate_schema_state(
    existing_tables: List[str],
    existing_views: List[str],
    applied_migrations: List[Tuple[str, str]],
    can_create_in_public: bool,
    installed_extensions: Dict[str, str],
    available_extensions: Set[str],
    pg_version_num: int,
) -> Tuple[str, str, int, List[str]]:
    """
    Avalia o estado estrutural do banco e retorna (status, mensagem, exit_code, motivos).
    Status possíveis:
      - READY_FOR_BASELINE (0) [Avaliação Preliminar]
      - ALREADY_PROVISIONED (0)
      - PARTIAL_STATE (2)
      - MANUAL_REVIEW_REQUIRED (2)
    """
    existing_tables_set = set(t.lower() for t in existing_tables)
    existing_views_set = set(v.lower() for v in existing_views)

    sosp_present = existing_tables_set.intersection(SOSP_EXPECTED_TABLES)
    django_present = existing_tables_set.intersection(DJANGO_CORE_TABLES)
    unknown_tables = existing_tables_set - (SOSP_EXPECTED_TABLES | DJANGO_CORE_TABLES)
    unknown_views = existing_views_set - SOSP_EXPECTED_VIEWS
    sosp_views_present = existing_views_set.intersection(SOSP_EXPECTED_VIEWS)

    applied_set = set((app, name) for app, name in applied_migrations)
    expected_set = set(EXPECTED_BASELINE_MIGRATIONS)

    issues: List[str] = []

    # 1. Verificação de Versão PostgreSQL (>= 17 recomendada)
    if pg_version_num < 160000:
        issues.append(f"Versão PostgreSQL muito antiga ({pg_version_num}). O SOSP requer PostgreSQL 17.")

    # 2. Verificação de Extensões
    for req_ext in ("pg_trgm", "unaccent"):
        if req_ext not in installed_extensions and req_ext not in available_extensions:
            issues.append(f"Extensão obrigatória '{req_ext}' não está instalada nem disponível no servidor PostgreSQL.")

    # 3. Verificação de Privilégios DDL
    if not can_create_in_public:
        issues.append("Usuário conectado NÃO possui permissão CREATE no schema 'public' (não pode executar migrations).")

    # 4. Avaliação de Conflitos e Tabelas Desconhecidas
    if unknown_tables:
        issues.append(f"Detectadas {len(unknown_tables)} tabelas desconhecidas no schema 'public': {sorted(list(unknown_tables))[:10]}")

    if unknown_views:
        issues.append(f"Detectadas {len(unknown_views)} views desconhecidas no schema 'public': {sorted(list(unknown_views))[:10]}")

    # Cenário 1: Banco Limpo (READY_FOR_BASELINE) - Avaliação Preliminar
    # Exige: 0 tabelas SOSP, 0 tabelas Django, 0 tabelas desconhecidas, 0 views SOSP, 0 migrations registradas
    if len(existing_tables_set) == 0 and len(existing_views_set) == 0 and len(applied_migrations) == 0:
        if issues:
            return (
                "MANUAL_REVIEW_REQUIRED",
                "Banco está vazio de tabelas, mas apresenta problemas de privilégio/versão/extensões.",
                2,
                issues,
            )
        return (
            "READY_FOR_BASELINE",
            (
                "Avaliação preliminar: Banco de dados limpo e sem conflitos aparentes no schema 'public'. "
                "ATENÇÃO: Este status é uma avaliação preliminar de não-conflito, NÃO constituindo autorização "
                "automática para execução de migrations sem aprovação do Tech Lead."
            ),
            0,
            [],
        )

    # Cenário 2: Base Totalmente Implantada (ALREADY_PROVISIONED)
    # Exige: exatamente as 36 tabelas SOSP, 2 views, todas as 11 migrações aplicadas e 0 tabelas desconhecidas
    if (
        len(sosp_present) == len(SOSP_EXPECTED_TABLES)
        and len(sosp_views_present) == len(SOSP_EXPECTED_VIEWS)
        and expected_set.issubset(applied_set)
        and not unknown_tables
        and not unknown_views
    ):
        if issues:
            return (
                "MANUAL_REVIEW_REQUIRED",
                "Tabelas do SOSP e migrações estão presentes, mas há pendências de revisão.",
                2,
                issues,
            )
        return (
            "ALREADY_PROVISIONED",
            (
                f"Todas as 36 tabelas de aplicação, 2 views e {len(EXPECTED_BASELINE_MIGRATIONS)} migrações da baseline estão registradas. "
                "Nota: contagens de objetos atestam presença física, devendo a integridade semântica "
                "ser garantida pela suíte de testes de integração."
            ),
            0,
            [],
        )

    # Cenário 3: Tabelas ou views desconhecidas / conflitos externos (MANUAL_REVIEW_REQUIRED)
    if unknown_tables or unknown_views or issues:
        reasons = list(issues)
        if unknown_tables:
            reasons.append(f"Schema 'public' contém tabelas não pertencentes ao SOSP ({len(unknown_tables)} tabelas).")
        if unknown_views:
            reasons.append(f"Schema 'public' contém views desconhecidas ({len(unknown_views)} views).")
        return (
            "MANUAL_REVIEW_REQUIRED",
            "Ambiente com divergências estruturais ou objetos não identificados que exigem avaliação humana.",
            2,
            reasons,
        )

    # Cenário 4: Estado Parcial (PARTIAL_STATE)
    # Algumas tabelas do SOSP existem ou algumas migrações foram aplicadas
    if len(sosp_present) > 0 or len(applied_migrations) > 0:
        reasons = list(issues)
        if len(sosp_present) < len(SOSP_EXPECTED_TABLES):
            reasons.append(f"Apenas {len(sosp_present)} de {len(SOSP_EXPECTED_TABLES)} tabelas SOSP estão presentes.")
        if not expected_set.issubset(applied_set):
            missing_migs = expected_set - applied_set
            reasons.append(f"Faltam {len(missing_migs)} migrações da baseline: {sorted(list(missing_migs))}")
        if len(sosp_views_present) < len(SOSP_EXPECTED_VIEWS):
            reasons.append(f"Apenas {len(sosp_views_present)} de {len(SOSP_EXPECTED_VIEWS)} views SOSP presentes.")
        return (
            "PARTIAL_STATE",
            "Estado parcialmente provisionado ou inconsistente. Não aplique migrations automáticas.",
            2,
            reasons,
        )

    # Cenário 5: Fallback genérico para revisão manual
    reasons = list(issues)
    if "django_migrations" in existing_tables_set and len(sosp_present) == 0:
        reasons.append("Tabela 'django_migrations' existe, mas nenhuma tabela do SOSP foi encontrada.")

    return (
        "MANUAL_REVIEW_REQUIRED",
        "Ambiente com divergências estruturais que exigem avaliação humana antes de prosseguir.",
        2,
        reasons,
    )


def inspect_database(conn_info: Dict[str, Any]) -> int:
    try:
        import psycopg
    except ImportError:
        print("✗ Erro: Biblioteca 'psycopg' não encontrada. Instale via requirements.txt.")
        return 1

    # Força transação em modo estritamente somente-leitura na conexão
    conn_info["options"] = "-c default_transaction_read_only=on"

    try:
        with psycopg.connect(**conn_info) as conn:
            with conn.cursor() as cur:
                print("✓ Conexão estabelecida em modo SOMENTE LEITURA (default_transaction_read_only=on).\n")

                # 1. Informações da Instância e Sessão
                cur.execute("SELECT current_database(), current_user, session_user, version(), current_setting('server_version_num');")
                db_name, cur_user, sess_user, version_str, ver_num_str = cur.fetchone()
                pg_version_num = int(ver_num_str)

                print("1. AMBIENTE E SESSÃO ATIVA")
                print(f"   - Banco:    {db_name}")
                print(f"   - Usuário:  {cur_user} (Session: {sess_user})")
                print(f"   - Versão:   {version_str.split(',')[0]} (num: {pg_version_num})")

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

                # 3. Extensões Instaladas e Disponíveis
                print("\n3. EXTENSÕES POSTGRESQL")
                cur.execute("SELECT extname, extversion FROM pg_extension ORDER BY extname;")
                installed_extensions = dict(cur.fetchall())
                for ext, ver in installed_extensions.items():
                    print(f"   - Instalada:  {ext:<15} (versão {ver})")

                cur.execute("SELECT name FROM pg_available_extensions WHERE name IN ('unaccent', 'pg_trgm');")
                available_extensions = set(r[0] for r in cur.fetchall())
                for ext in ("unaccent", "pg_trgm"):
                    if ext in installed_extensions:
                        print(f"   ✓ Extensão '{ext}' está ativa.")
                    elif ext in available_extensions:
                        print(f"   ℹ️  Extensão '{ext}' disponível para instalação via migration.")
                    else:
                        print(f"   ✗ Extensão '{ext}' NÃO encontrada no catálogo de extensões!")

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
                django_present = set(existing_tables).intersection(DJANGO_CORE_TABLES)
                unknown_tables = set(existing_tables) - (SOSP_EXPECTED_TABLES | DJANGO_CORE_TABLES)

                print(f"   - Tabelas de domínio SOSP presentes: {len(sosp_present)} de {len(SOSP_EXPECTED_TABLES)}")
                print(f"   - Tabelas técnicas Django presentes: {len(django_present)} de {len(DJANGO_CORE_TABLES)}")
                if unknown_tables:
                    print(f"   ⚠️  Tabelas desconhecidas encontradas: {len(unknown_tables)}")

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
                    status_view = "✓ SOSP" if v in SOSP_EXPECTED_VIEWS else "⚠️  Desconhecida"
                    print(f"   - View: {v:<35} [{status_view}]")

                # 6. Histórico de Migrations do Django
                print("\n6. HISTÓRICO DE MIGRATIONS (django_migrations)")
                applied_migrations: List[Tuple[str, str]] = []
                if "django_migrations" in existing_tables:
                    cur.execute("SELECT app, name, applied FROM django_migrations ORDER BY applied;")
                    rows = cur.fetchall()
                    applied_migrations = [(r[0], r[1]) for r in rows]
                    print(f"   - Total de migrations aplicadas: {len(applied_migrations)}")
                    for app, name, applied in rows:
                        print(f"     * {app:<15} {name:<30} ({applied.strftime('%Y-%m-%d %H:%M:%S')})")
                else:
                    print("   - Tabela 'django_migrations' não existe no banco (Banco inicial limpo).")

                # 7. Diagnóstico de RLS (Row Level Security)
                print("\n7. STATUS DE RLS NAS TABELAS DO SCHEMA 'public'")
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

                status, msg, exit_code, issues = evaluate_schema_state(
                    existing_tables=existing_tables,
                    existing_views=existing_views,
                    applied_migrations=applied_migrations,
                    can_create_in_public=can_create_in_public,
                    installed_extensions=installed_extensions,
                    available_extensions=available_extensions,
                    pg_version_num=pg_version_num,
                )

                if status == "READY_FOR_BASELINE":
                    print("🟢 STATUS: PRONTO PARA IMPLANTAÇÃO INICIAL (READY_FOR_BASELINE) [AVALIAÇÃO PRELIMINAR]")
                    print("   [!] GOVERNANÇA: Este status é uma avaliação preliminar de não-conflito.")
                    print("       NÃO constitui autorização automática para executar migrations.")
                    print("       Contagens de objetos não comprovam sozinhas a integridade semântica completa.")
                elif status == "ALREADY_PROVISIONED":
                    print("🔵 STATUS: BASE TOTALMENTE IMPLANTADA (ALREADY_PROVISIONED)")
                elif status == "PARTIAL_STATE":
                    print("🟡 STATUS: ESTADO PARCIAL DETECTADO (PARTIAL_STATE)")
                else:
                    print("⚠️ STATUS: REVISÃO MANUAL OBRIGATÓRIA (MANUAL_REVIEW_REQUIRED)")

                print(f"   Descrição: {msg}")
                if issues:
                    print("   Pendências / Riscos identificados:")
                    for issue in issues:
                        print(f"     * {issue}")

                print("=" * 70)
                return exit_code

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
    parser.add_argument(
        "--sslmode",
        default="",
        help="Modo SSL ('require', 'verify-ca', 'verify-full' para remoto; padrão 'require' em remoto, 'prefer' em local)",
    )

    args = parser.parse_args()

    # Validação e aplicação de regras de SSL para hosts remotos
    is_remote = args.host not in ("localhost", "127.0.0.1", "") and not args.host.startswith("/")
    raw_sslmode = args.sslmode or os.environ.get("DB_SSLMODE") or ("require" if is_remote else "prefer")
    try:
        sslmode = validate_sslmode(raw_sslmode, args.host)
    except ValueError as e:
        print(f"\n❌ ERRO DE GOVERNANÇA DE SEGURANÇA SSL:\n   {e}\n")
        sys.exit(1)

    password = resolve_password(args.host)

    conn_info = {
        "host": args.host,
        "port": args.port,
        "dbname": args.dbname,
        "user": args.user,
        "password": password,
        "sslmode": sslmode,
        "connect_timeout": 8,
    }

    print("=" * 70)
    print("SOSP — Pré-Voo: Inspeção de Schemas e Tabelas (Somente Leitura)")
    print("=" * 70)
    print(f"Host:     {mask_string(args.host)}")
    print(f"Porta:    {args.port}")
    print(f"Base:     {args.dbname}")
    print(f"Usuário:  {mask_string(args.user)}")
    print(f"SSL Mode: {sslmode}")
    print("-" * 70)

    exit_code = inspect_database(conn_info)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
