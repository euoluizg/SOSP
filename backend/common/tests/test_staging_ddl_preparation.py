"""
SOSP — Testes Automatizados da Preparação da Tarefa 1 (DDL Supabase Staging).

Valida:
1. Conformidade de segurança e idempotência em scripts/staging_ddl/02_apply_schema.sql.
2. Alinhamento exato de 100% dos modelos Django e colunas com o schema SQL.
3. Resolução segura de parâmetros e TLS em 01_preflight_check.py.
4. Mecanismo de defesa de dry-run e trava de confirmação humana em 02_apply_staging_ddl.py.
5. Verificação pós-voo de integridade e privilégios em 03_postflight_verify.py.
"""

import os
import re
import pytest
from django.apps import apps

# Caminhos canônicos
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
DDL_FILE_PATH = os.path.join(BASE_DIR, "scripts/staging_ddl/02_apply_schema.sql")
SCHEMA_DOC_PATH = os.path.join(BASE_DIR, "docs/database/schema.sql")

EXPECTED_36_TABLES = [
    "accountsGender", "accountsCitizen", "accountsInternalUser", "accountsSession",
    "accountsLoginAttempt", "accountsPasswordReset", "catalogAgency", "catalogUnit",
    "catalogUnitOpeningHour", "catalogNonWorkingDay", "catalogService", "catalogServiceAgency",
    "catalogUnitService", "catalogServiceStep", "catalogServiceDocument", "catalogFaq",
    "catalogServiceVersion", "searchQueryLog", "searchSynonym", "guidanceProgress",
    "guidanceGeneratedPdf", "schedulingSlot", "schedulingAppointment", "schedulingProtocol",
    "schedulingProtocolAttachment", "schedulingProtocolTransition", "feedbackReview",
    "feedbackReviewReport", "feedbackQuestion", "notificationsTemplate", "notificationsPreference",
    "notificationsDelivery", "notificationsPushSubscription", "reportsExport", "auditEvent",
    "auditDataSubjectRequest"
]


def test_ddl_file_exists_and_matches_docs_schema():
    """Confirma existência do arquivo DDL de staging e sincronização com docs/database/schema.sql."""
    assert os.path.isfile(DDL_FILE_PATH), f"Arquivo não encontrado: {DDL_FILE_PATH}"
    assert os.path.isfile(SCHEMA_DOC_PATH), f"Arquivo não encontrado: {SCHEMA_DOC_PATH}"

    with open(DDL_FILE_PATH, "r", encoding="utf-8") as f1, open(SCHEMA_DOC_PATH, "r", encoding="utf-8") as f2:
        content_ddl = f1.read()
        content_doc = f2.read()

    # Ambos devem conter o schema sosp_security e a função de auth
    assert "CREATE SCHEMA IF NOT EXISTS sosp_security;" in content_ddl
    assert "CREATE SCHEMA IF NOT EXISTS sosp_security;" in content_doc
    assert "sosp_security.authenticate_citizen_by_cpf" in content_ddl
    assert "sosp_security.authenticate_citizen_by_cpf" in content_doc


def test_ddl_identifiers_use_unquoted_camelcase_and_zero_destructive_statements():
    """Valida ADR-002 (camelCase sem aspas) e ausência total de DROP TABLE ou TRUNCATE (RN-40, RS-05)."""
    with open(DDL_FILE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Zero aspas duplas em identificadores
    assert '"' not in content, "FALHA ADR-002: Identificadores não podem conter aspas duplas."

    # Remove comentários para validar ausência de comandos destrutivos no SQL executável
    clean_lines = [line for line in content.splitlines() if not line.strip().startswith("--")]
    executable_sql = "\n".join(clean_lines).upper()

    # Zero DROP TABLE ou TRUNCATE executável
    assert not re.search(r"\bDROP\s+TABLE\b", executable_sql), "FALHA DE SEGURANÇA: DROP TABLE é expressamente proibido."
    assert not re.search(r"\bTRUNCATE\b", executable_sql), "FALHA DE SEGURANÇA: TRUNCATE é expressamente proibido."

    # Todas as 36 tabelas devem usar CREATE TABLE IF NOT EXISTS
    for table_name in EXPECTED_36_TABLES:
        pattern = rf"CREATE TABLE IF NOT EXISTS\s+{table_name}\b"
        assert re.search(pattern, content, re.IGNORECASE), f"Tabela {table_name} deve usar CREATE TABLE IF NOT EXISTS"


def test_ddl_security_functions_have_security_definer_and_restricted_search_path():
    """Valida requisitos de AppSec para funções em sosp_security e setUpdatedAt."""
    with open(DDL_FILE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # setUpdatedAt com search_path restrito
    assert "CREATE OR REPLACE FUNCTION setUpdatedAt()" in content
    assert "SET search_path = pg_catalog, public" in content

    # authenticate_citizen_by_cpf com SECURITY DEFINER e search_path restrito
    assert "CREATE OR REPLACE FUNCTION sosp_security.authenticate_citizen_by_cpf" in content
    assert "SECURITY DEFINER" in content
    assert "REVOKE ALL ON FUNCTION sosp_security.authenticate_citizen_by_cpf(VARCHAR) FROM PUBLIC;" in content

    # Validação de parâmetro por regex
    assert "^[0-9]{11}$" in content


def test_ddl_enables_row_level_security_on_all_36_tables():
    """Confirma que todas as 36 tabelas possuem ALTER TABLE ... ENABLE ROW LEVEL SECURITY."""
    with open(DDL_FILE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    for table_name in EXPECTED_36_TABLES:
        pattern = rf"ALTER TABLE\s+{table_name}\s+ENABLE ROW LEVEL SECURITY;"
        assert re.search(pattern, content, re.IGNORECASE), f"RLS não habilitado para {table_name}"


def test_ddl_analytical_views_use_security_invoker():
    """Confirma que ambas as views analíticas utilizam security_invoker = true."""
    with open(DDL_FILE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert "CREATE OR REPLACE VIEW vw_catalogServiceSearch WITH (security_invoker = true)" in content
    assert "CREATE OR REPLACE VIEW vw_schedulingSlotAvailability WITH (security_invoker = true)" in content


def test_django_models_100_percent_aligned_with_ddl_columns():
    """Compara campo a campo todos os modelos de domínio do Django contra as tabelas do DDL."""
    with open(DDL_FILE_PATH, "r", encoding="utf-8") as f:
        sql = f.read()

    schema_tables = {}
    table_blocks = re.findall(r'CREATE TABLE IF NOT EXISTS\s+([a-zA-Z0-9_]+)\s*\((.*?)\n  \);', sql, re.DOTALL)
    for tname, body in table_blocks:
        cols = []
        for line in body.splitlines():
            line = line.strip()
            if not line or line.startswith('--') or line.startswith('CONSTRAINT') or line.startswith('PRIMARY KEY'):
                continue
            col_match = re.match(r'([a-zA-Z0-9_]+)\s+[a-zA-Z0-9_]+', line)
            if col_match:
                cols.append(col_match.group(1).lower())
        schema_tables[tname.lower()] = cols

    # Validações
    assert len(schema_tables) == 36, f"Esperadas 36 tabelas no DDL, encontradas {len(schema_tables)}"

    missing_fields = []
    for model in apps.get_models():
        if model._meta.app_label in ('admin', 'auth', 'contenttypes', 'sessions', 'messages'):
            continue
        tname = model._meta.db_table.lower()
        if model._meta.managed is False:
            continue  # Views unmanaged
        if tname not in schema_tables:
            missing_fields.append(f"Tabela {tname} de {model.__name__} ausente no DDL")
            continue

        s_cols = schema_tables[tname]
        for field in model._meta.concrete_fields:
            col_name = (field.column or field.name).lower()
            if col_name not in s_cols:
                missing_fields.append(f"{model.__name__}.{field.name} (coluna '{col_name}') não encontrada em {tname}")

    assert missing_fields == [], f"Divergências encontradas entre Django ORM e DDL: {missing_fields}"


def test_preflight_script_mock_and_sslmode_validation():
    """Testa a execução de simulação do script 01_preflight_check.py e regras de SSL."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "preflight_check",
        os.path.join(BASE_DIR, "scripts/staging_ddl/01_preflight_check.py")
    )
    preflight_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(preflight_mod)

    validate_sslmode = preflight_mod.validate_sslmode
    run_preflight_inspection = preflight_mod.run_preflight_inspection
    parse_connection_params = preflight_mod.parse_connection_params

    # 1. Validação de SSL
    remote_host = "aws-1-sa-east-1.pooler.supabase.com"
    assert validate_sslmode("require", remote_host) == "require"
    assert validate_sslmode("verify-full", remote_host) == "verify-full"
    with pytest.raises(ValueError, match="inseguro"):
        validate_sslmode("disable", remote_host)
    with pytest.raises(ValueError, match="inseguro"):
        validate_sslmode("prefer", remote_host)

    # Host local aceita disable
    assert validate_sslmode("disable", "localhost") == "disable"

    # 2. Execução mock
    params = parse_connection_params()
    report = run_preflight_inspection(params, mock_mode=True)
    assert report["is_read_only"] is True
    assert report["status"] == "CLEAN_SLATE_READY_FOR_BASELINE"
    assert report["has_sosp_security"] is True
    assert len(report["missing_sosp_tables"]) == 36


def test_apply_script_dry_run_and_safety_gate():
    """Testa que 02_apply_staging_ddl.py rejeita apply sem confirmação explícita."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "apply_staging_ddl",
        os.path.join(BASE_DIR, "scripts/staging_ddl/02_apply_staging_ddl.py")
    )
    apply_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(apply_mod)

    execute_ddl = apply_mod.execute_ddl
    parse_connection_params = apply_mod.parse_connection_params

    params = parse_connection_params()

    # 1. Modo mock em dry-run
    res_dry = execute_ddl(DDL_FILE_PATH, params, dry_run=True, mock_mode=True)
    assert res_dry["success"] is True
    assert res_dry["action"] == "ROLLBACK"

    # 2. Modo mock em apply confirmado
    res_apply = execute_ddl(DDL_FILE_PATH, params, dry_run=False, confirm_apply=True, mock_mode=True)
    assert res_apply["success"] is True
    assert res_apply["action"] == "COMMIT"

    # 3. Tentativa de apply sem confirmação deve lançar PermissionError
    with pytest.raises(PermissionError, match="autorização explícita"):
        execute_ddl(DDL_FILE_PATH, params, dry_run=False, confirm_apply=False, mock_mode=False)


def test_postflight_script_mock_verification():
    """Testa o script 03_postflight_verify.py em modo mock."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "postflight_verify",
        os.path.join(BASE_DIR, "scripts/staging_ddl/03_postflight_verify.py")
    )
    post_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(post_mod)

    run_postflight_verification = post_mod.run_postflight_verification
    parse_connection_params = post_mod.parse_connection_params

    params = parse_connection_params()
    audit = run_postflight_verification(params, mock_mode=True)

    assert audit["all_checks_passed"] is True
    assert audit["tables_found"] == 36
    assert audit["views_found"] == 2
    assert audit["rls_enabled_count"] == 36
    assert audit["has_sosp_security"] is True
    assert audit["has_auth_fn"] is True
    assert audit["auth_fn_is_security_definer"] is True
    assert audit["auth_fn_public_revoked"] is True
    assert audit["triggers_active_count"] == 14
