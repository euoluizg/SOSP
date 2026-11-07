"""
SOSP — Testes Automatizados para os Scripts de Pré-Voo (Etapa 4A / Hardened).

Valida:
1. Resolução segura de senhas (exclusivamente via env ou getpass, sem flag CLI --password).
2. Validação estrita de sslmode para conexões remotas (require ou superior, sem fallback para prefer/disable).
3. Compatibilidade de sslmode com bancos locais (disable/prefer permitidos).
4. Rejeição da opção CLI --password.
5. Diagnóstico de schema: READY_FOR_BASELINE preliminar, detecção de conflitos, falso positivo, ALREADY_PROVISIONED.
"""

import os
import sys
import subprocess
import pytest

from scripts.preflight_schema_inspection import (
    evaluate_schema_state,
    validate_sslmode as validate_sslmode_schema,
    resolve_password as resolve_password_schema,
    enter_verified_readonly_transaction as enter_ro_schema,
    safe_rollback as safe_rollback_schema,
    inspect_database,
    run_verified_readonly_migrate_plan,
    SOSP_EXPECTED_TABLES,
    SOSP_EXPECTED_VIEWS,
    EXPECTED_BASELINE_MIGRATIONS,
    DJANGO_CORE_TABLES,
)
from scripts.preflight_connectivity import (
    validate_sslmode as validate_sslmode_conn,
    resolve_password as resolve_password_conn,
    enter_verified_readonly_transaction as enter_ro_conn,
    safe_rollback as safe_rollback_conn,
    test_postgresql_handshake as check_pg_handshake,
    mask_string,
)


def test_mask_string():
    """Valida o mascaramento de strings sensíveis."""
    assert mask_string("") == "[NÃO DEFINIDO]"
    assert mask_string("abc") == "***"
    masked = mask_string("aws-1-sa-east-1.pooler.supabase.com")
    assert masked.startswith("aws-")
    assert masked.endswith(".com")
    assert "..." in masked


def test_resolve_password_priority(monkeypatch):
    """Testa a cadeia de resolução segura de senhas via variáveis de ambiente."""
    db_pwd_var = "DB_" + "PASSWORD"
    pg_pwd_var = "PG" + "PASSWORD"

    # 1. Prioridade para DB_PASSWORD sobre PGPASSWORD
    monkeypatch.setenv(db_pwd_var, "env_test_val")
    monkeypatch.setenv(pg_pwd_var, "pg_test_val")
    assert resolve_password_conn("localhost") == "env_test_val"
    assert resolve_password_schema("localhost") == "env_test_val"

    # 2. PGPASSWORD quando DB_PASSWORD não existe
    monkeypatch.delenv(db_pwd_var)
    assert resolve_password_conn("localhost") == "pg_test_val"
    assert resolve_password_schema("localhost") == "pg_test_val"

    # 3. Sem senha em host remoto e stdin não-tty (não deve quebrar com crash)
    monkeypatch.delenv(pg_pwd_var)
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    assert resolve_password_conn("aws-1-sa-east-1.pooler.supabase.com") == ""
    assert resolve_password_schema("aws-1-sa-east-1.pooler.supabase.com") == ""


def test_remote_host_sslmode_restrictions():
    """Conexões remotas exigem 'require', 'verify-ca' ou 'verify-full'. Proíbem disable/prefer."""
    remote_host = "aws-1-sa-east-1.pooler.supabase.com"

    for func in (validate_sslmode_conn, validate_sslmode_schema):
        # Modos aceitos em remoto
        assert func("require", remote_host) == "require"
        assert func("verify-ca", remote_host) == "verify-ca"
        assert func("verify-full", remote_host) == "verify-full"
        assert func("REQUIRE", remote_host) == "require"

        # Modos proibidos em remoto
        for forbidden in ("disable", "prefer", "allow"):
            with pytest.raises(ValueError, match="Conexão remota rejeitada por governança de segurança"):
                func(forbidden, remote_host)


def test_local_host_sslmode_compatibility():
    """Conexões locais (localhost, 127.0.0.1, socket Unix) preservam compatibilidade com prefer/disable."""
    local_hosts = ("localhost", "127.0.0.1", "/tmp")

    for func in (validate_sslmode_conn, validate_sslmode_schema):
        for host in local_hosts:
            assert func("disable", host) == "disable"
            assert func("prefer", host) == "prefer"
            assert func("require", host) == "require"


def test_cli_password_argument_removed():
    """Garante que a opção CLI de senha foi totalmente removida dos scripts e gera erro se invocada."""
    scripts_to_test = [
        "scripts/preflight_connectivity.py",
        "scripts/preflight_schema_inspection.py",
    ]
    base_dir = os.path.join(os.path.dirname(__file__), "../../../backend")
    pwd_flag = "--" + "password"

    for script in scripts_to_test:
        cmd = [sys.executable, script, pwd_flag]
        res = subprocess.run(cmd, cwd=base_dir, capture_output=True, text=True)
        assert res.returncode != 0
        assert "unrecognized arguments" in res.stderr


def test_evaluate_schema_clean_ready_for_baseline():
    """Banco completamente vazio de tabelas deve retornar READY_FOR_BASELINE preliminar com código 0."""
    status, msg, code, issues = evaluate_schema_state(
        existing_tables=[],
        existing_views=[],
        applied_migrations=[],
        can_create_in_public=True,
        installed_extensions={"plpgsql": "1.0"},
        available_extensions={"pg_trgm", "unaccent"},
        pg_version_num=170000,
    )
    assert status == "READY_FOR_BASELINE"
    assert code == 0
    assert len(issues) == 0
    assert "Avaliação preliminar" in msg
    assert "NÃO constituindo autorização automática" in msg


def test_evaluate_schema_clean_but_no_ddl_permission():
    """Banco vazio, porém usuário sem permissão CREATE no schema public -> MANUAL_REVIEW_REQUIRED."""
    status, msg, code, issues = evaluate_schema_state(
        existing_tables=[],
        existing_views=[],
        applied_migrations=[],
        can_create_in_public=False,
        installed_extensions={"plpgsql": "1.0"},
        available_extensions={"pg_trgm", "unaccent"},
        pg_version_num=170000,
    )
    assert status == "MANUAL_REVIEW_REQUIRED"
    assert code == 2
    assert any("CREATE no schema 'public'" in i for i in issues)


def test_evaluate_schema_clean_but_missing_extensions():
    """Banco vazio, porém extensões essenciais pg_trgm/unaccent indisponíveis no PostgreSQL."""
    status, msg, code, issues = evaluate_schema_state(
        existing_tables=[],
        existing_views=[],
        applied_migrations=[],
        can_create_in_public=True,
        installed_extensions={"plpgsql": "1.0"},
        available_extensions=set(),  # Nenhuma extensão disponível
        pg_version_num=170000,
    )
    assert status == "MANUAL_REVIEW_REQUIRED"
    assert code == 2
    assert any("Extensão obrigatória 'pg_trgm'" in i for i in issues)


def test_evaluate_schema_false_positive_unknown_tables():
    """Prevenção de falso positivo: schema tem tabelas legadas/estranhas (ex.: users, items)."""
    status, msg, code, issues = evaluate_schema_state(
        existing_tables=["legacy_app_users", "orders"],
        existing_views=[],
        applied_migrations=[],
        can_create_in_public=True,
        installed_extensions={"plpgsql": "1.0", "pg_trgm": "1.6", "unaccent": "1.1"},
        available_extensions={"pg_trgm", "unaccent"},
        pg_version_num=170000,
    )
    assert status == "MANUAL_REVIEW_REQUIRED"
    assert code == 2
    assert any("tabelas desconhecidas" in i for i in issues)


def test_evaluate_schema_inconsistent_django_migrations_without_tables():
    """Prevenção de falso positivo: django_migrations existe mas nenhuma tabela SOSP existe."""
    status, msg, code, issues = evaluate_schema_state(
        existing_tables=["django_migrations"],
        existing_views=[],
        applied_migrations=[("accounts", "0001_initial")],
        can_create_in_public=True,
        installed_extensions={"plpgsql": "1.0", "pg_trgm": "1.6", "unaccent": "1.1"},
        available_extensions={"pg_trgm", "unaccent"},
        pg_version_num=170000,
    )
    assert status == "PARTIAL_STATE"
    assert code == 2


def test_evaluate_schema_partial_tables():
    """Banco com apenas algumas tabelas criadas deve retornar PARTIAL_STATE."""
    partial_tables = ["accountsgender", "accountscitizen", "catalogagency"]
    status, msg, code, issues = evaluate_schema_state(
        existing_tables=partial_tables,
        existing_views=[],
        applied_migrations=[],
        can_create_in_public=True,
        installed_extensions={"plpgsql": "1.0", "pg_trgm": "1.6", "unaccent": "1.1"},
        available_extensions={"pg_trgm", "unaccent"},
        pg_version_num=170000,
    )
    assert status == "PARTIAL_STATE"
    assert code == 2
    assert any("Apenas 3 de 36 tabelas SOSP estão presentes" in i for i in issues)


def test_evaluate_schema_fully_provisioned():
    """Banco com todas as 36 tabelas, 2 views e 11 migrações deve retornar ALREADY_PROVISIONED com código 0."""
    all_tables = list(SOSP_EXPECTED_TABLES) + list(DJANGO_CORE_TABLES)
    status, msg, code, issues = evaluate_schema_state(
        existing_tables=all_tables,
        existing_views=list(SOSP_EXPECTED_VIEWS),
        applied_migrations=EXPECTED_BASELINE_MIGRATIONS,
        can_create_in_public=True,
        installed_extensions={"plpgsql": "1.0", "pg_trgm": "1.6", "unaccent": "1.1"},
        available_extensions={"pg_trgm", "unaccent"},
        pg_version_num=170000,
    )
    assert status == "ALREADY_PROVISIONED"
    assert code == 0
    assert len(issues) == 0


def test_evaluate_schema_provisioned_with_conflicting_extra_table():
    """Se tiver todas as 36 tabelas mas também uma tabela desconhecida, requer revisão manual."""
    all_tables = list(SOSP_EXPECTED_TABLES) + list(DJANGO_CORE_TABLES) + ["unauthorized_shadow_table"]
    status, msg, code, issues = evaluate_schema_state(
        existing_tables=all_tables,
        existing_views=list(SOSP_EXPECTED_VIEWS),
        applied_migrations=EXPECTED_BASELINE_MIGRATIONS,
        can_create_in_public=True,
        installed_extensions={"plpgsql": "1.0", "pg_trgm": "1.6", "unaccent": "1.1"},
        available_extensions={"pg_trgm", "unaccent"},
        pg_version_num=170000,
    )
    assert status == "MANUAL_REVIEW_REQUIRED"
    assert code == 2
    assert any("tabelas desconhecidas" in i for i in issues)


class _FakeCursor:
    """Cursor simulado para validar a sequência exata de comandos SQL em pré-voo."""

    def __init__(self, tx_read_only_value: str = "on", fail_on_query: str = ""):
        self.tx_read_only_value = tx_read_only_value
        self.fail_on_query = fail_on_query
        self.executed_sql: list[str] = []
        self._last_sql = ""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def execute(self, sql: str, params=None):
        normalized = " ".join(sql.strip().split())
        self.executed_sql.append(normalized)
        self._last_sql = normalized
        if self.fail_on_query and self.fail_on_query in normalized:
            raise RuntimeError(f"Erro simulado na query: {self.fail_on_query}")

    def fetchone(self):
        if "SHOW transaction_read_only" in self._last_sql:
            return (self.tx_read_only_value,)
        if "SELECT version()" in self._last_sql:
            return ("PostgreSQL 17.11 on aarch64-unknown-linux-gnu", "postgres", "postgres", "170011")
        if "has_schema_privilege" in self._last_sql:
            return (True,)
        return ("ok",)

    def fetchall(self):
        if "pg_extension" in self._last_sql:
            return [("plpgsql", "1.0")]
        if "pg_available_extensions" in self._last_sql:
            return [("pg_trgm",), ("unaccent",)]
        return []


class _FakePgConn:
    def __init__(self, ssl_in_use: bool = True):
        self.ssl_in_use = ssl_in_use


class _FakeConn:
    def __init__(self, cursor: _FakeCursor, ssl_in_use: bool = True):
        self._cursor = cursor
        self.pgconn = _FakePgConn(ssl_in_use=ssl_in_use)
        self.connect_kwargs: dict = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def cursor(self):
        return self._cursor


def test_enter_verified_readonly_transaction_success_and_rollback():
    """
    Valida que enter_verified_readonly_transaction inicia explicitamente BEGIN READ ONLY,
    consulta SHOW transaction_read_only na transação ativa, exige 'on' e encerra com ROLLBACK.
    """
    for enter_fn, rollback_fn in ((enter_ro_conn, safe_rollback_conn), (enter_ro_schema, safe_rollback_schema)):
        cur = _FakeCursor(tx_read_only_value="on")
        tx_ro = enter_fn(cur)
        assert tx_ro == "on"
        rollback_fn(cur)
        assert cur.executed_sql == [
            "BEGIN READ ONLY;",
            "SHOW transaction_read_only;",
            "ROLLBACK;",
        ]


def test_abort_immediately_when_transaction_remains_read_write(monkeypatch, capsys):
    """
    Garante interrupção imediata quando a transação permanece READ WRITE (transaction_read_only='off'),
    sem executar consultas de metadados e garantindo ROLLBACK no bloco finally.
    """
    # 1. Helper direto deve levantar RuntimeError imediato
    for enter_fn in (enter_ro_conn, enter_ro_schema):
        cur_rw = _FakeCursor(tx_read_only_value="off")
        with pytest.raises(RuntimeError, match="esperado transaction_read_only='on', obtido 'off'"):
            enter_fn(cur_rw)
        assert cur_rw.executed_sql == [
            "BEGIN READ ONLY;",
            "SHOW transaction_read_only;",
        ]

    # 2. test_postgresql_handshake deve abortar imediatamente antes de SELECT version() e executar ROLLBACK
    cur_handshake_rw = _FakeCursor(tx_read_only_value="off")
    fake_conn_handshake = _FakeConn(cur_handshake_rw, ssl_in_use=True)
    captured_connect_kwargs_handshake = {}

    def fake_connect_handshake(**kwargs):
        captured_connect_kwargs_handshake.update(kwargs)
        return fake_conn_handshake

    import psycopg

    monkeypatch.setattr(psycopg, "connect", fake_connect_handshake)
    result = check_pg_handshake(
        host="aws-1-sa-east-1.pooler.supabase.com",
        port=5432,
        dbname="postgres",
        user="postgres.ref",
        password="secret",
        sslmode="require",
        timeout_sec=10,
    )
    assert result is False
    assert captured_connect_kwargs_handshake.get("autocommit") is True
    assert "options" not in captured_connect_kwargs_handshake
    assert cur_handshake_rw.executed_sql == [
        "BEGIN READ ONLY;",
        "SHOW transaction_read_only;",
        "ROLLBACK;",
    ]

    # 3. inspect_database deve abortar imediatamente (código 1) sem consultar pg_tables nem imprimir falso positivo
    cur_inspect_rw = _FakeCursor(tx_read_only_value="off")
    fake_conn_inspect = _FakeConn(cur_inspect_rw, ssl_in_use=True)
    captured_connect_kwargs_inspect = {}

    def fake_connect_inspect(**kwargs):
        captured_connect_kwargs_inspect.update(kwargs)
        return fake_conn_inspect

    monkeypatch.setattr(psycopg, "connect", fake_connect_inspect)
    exit_code = inspect_database(
        {
            "host": "aws-1-sa-east-1.pooler.supabase.com",
            "port": 5432,
            "dbname": "postgres",
            "user": "postgres.ref",
            "password": "secret",
            "sslmode": "require",
            "connect_timeout": 10,
            "options": "-c default_transaction_read_only=on",
        }
    )
    out = capsys.readouterr().out
    assert exit_code == 1
    assert "Conexão estabelecida e verificada em modo SOMENTE LEITURA" not in out
    assert captured_connect_kwargs_inspect.get("autocommit") is True
    assert "options" not in captured_connect_kwargs_inspect
    assert cur_inspect_rw.executed_sql == [
        "BEGIN READ ONLY;",
        "SHOW transaction_read_only;",
        "ROLLBACK;",
    ]


def test_session_pooler_compatibility_and_rollback_on_error(monkeypatch):
    """
    Valida compatibilidade com Session Pooler (Supavisor):
    - Não depende de 'options' de inicialização (remove se presente);
    - Conecta com autocommit=True;
    - Executa BEGIN READ ONLY + SHOW transaction_read_only;
    - Executa ROLLBACK mesmo quando ocorre erro durante a consulta de metadados.
    """
    import psycopg

    cur_err = _FakeCursor(tx_read_only_value="on", fail_on_query="pg_tables")
    fake_conn = _FakeConn(cur_err, ssl_in_use=True)
    captured_kwargs = {}

    def fake_connect(**kwargs):
        captured_kwargs.update(kwargs)
        return fake_conn

    monkeypatch.setattr(psycopg, "connect", fake_connect)
    exit_code = inspect_database(
        {
            "host": "aws-1-sa-east-1.pooler.supabase.com",
            "port": 5432,
            "dbname": "postgres",
            "user": "postgres.ref",
            "password": "secret",
            "sslmode": "require",
            "connect_timeout": 10,
            "options": "-c default_transaction_read_only=on",
        }
    )
    assert exit_code == 1
    assert captured_kwargs.get("autocommit") is True
    assert "options" not in captured_kwargs
    assert cur_err.executed_sql[0] == "BEGIN READ ONLY;"
    assert cur_err.executed_sql[1] == "SHOW transaction_read_only;"
    assert cur_err.executed_sql[-1] == "ROLLBACK;"


def test_run_verified_readonly_migrate_plan_rejects_sqlite_fallback(monkeypatch):
    """
    Garante que run_verified_readonly_migrate_plan recusa execução caso a conexão Django
    esteja em fallback SQLite em vez de PostgreSQL real.
    """
    from django.db import connections

    monkeypatch.setitem(connections["default"].settings_dict, "ENGINE", "django.db.backends.sqlite3")
    with pytest.raises(RuntimeError, match="ENGINE esperado 'django.db.backends.postgresql'"):
        run_verified_readonly_migrate_plan(database="default", require_ssl=False)

