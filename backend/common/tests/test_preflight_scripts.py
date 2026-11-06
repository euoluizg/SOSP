"""
SOSP — Testes Automatizados para os Scripts de Pré-Voo (Etapa 4A / Hardened).

Valida a lógica diagnóstica de schema, prevenção de falsos positivos, detecção de estados
parciais ou conflitantes, e resolução segura de credenciais.
"""

import os
import sys
import pytest

from scripts.preflight_schema_inspection import (
    evaluate_schema_state,
    SOSP_EXPECTED_TABLES,
    SOSP_EXPECTED_VIEWS,
    EXPECTED_BASELINE_MIGRATIONS,
    DJANGO_CORE_TABLES,
)
from scripts.preflight_connectivity import resolve_password, mask_string


def test_mask_string():
    """Valida o mascaramento de strings sensíveis."""
    assert mask_string("") == "[NÃO DEFINIDO]"
    assert mask_string("abc") == "***"
    masked = mask_string("aws-1-sa-east-1.pooler.supabase.com")
    assert masked.startswith("aws-")
    assert masked.endswith(".com")
    assert "..." in masked


def test_resolve_password_priority(monkeypatch):
    """Testa a cadeia de resolução segura de senhas sem getpass interativo."""
    # 1. Prioridade para CLI argument
    monkeypatch.setenv("DB_PASSWORD", "env_password")
    assert resolve_password("cli_password") == "cli_password"

    # 2. Prioridade para DB_PASSWORD sobre PGPASSWORD
    monkeypatch.setenv("PGPASSWORD", "pg_password")
    assert resolve_password("", "localhost") == "env_password"

    # 3. PGPASSWORD quando DB_PASSWORD não existe
    monkeypatch.delenv("DB_PASSWORD")
    assert resolve_password("", "localhost") == "pg_password"

    # 4. Sem senha em host remoto e stdin não-tty (não deve quebrar com crash)
    monkeypatch.delenv("PGPASSWORD")
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    assert resolve_password("", "aws-1-sa-east-1.pooler.supabase.com") == ""


def test_evaluate_schema_clean_ready_for_baseline():
    """Banco completamente vazio de tabelas deve retornar READY_FOR_BASELINE com código 0."""
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
