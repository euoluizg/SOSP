"""Regressões do fallback institucional sob erros de PostgreSQL."""

from unittest.mock import patch
from uuid import uuid4

import pytest
from django.db import connection

from apps.accounts.repositories import (
    CitizenDjangoORMRepository,
    FunctionNotFoundError,
    _safe_atomic_block,
)


class SqlError(Exception):
    def __init__(self, message, sqlstate):
        super().__init__(message)
        self.sqlstate = sqlstate


class FakeCursor:
    def __init__(self, error):
        self.error = error
        self.queries = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, query, params):
        self.queries.append(query)
        if len(self.queries) == 1:
            raise self.error

    def fetchone(self):
        return (
            uuid4(), "Servidor", "servidor@exemplo.gov.br", "SSP-1", None,
            None, "server", False, "hash", True,
        )


@pytest.mark.parametrize(
    ("error", "fallback_expected", "missing_function"),
    [
        (SqlError('column "must_change_password" does not exist', "42703"), True, False),
        (SqlError('permission denied for schema sosp_security', "42501"), False, False),
        (SqlError('function sosp_security.authenticate_internal_user_by_cpf does not exist', "42883"), False, True),
    ],
)
def test_only_missing_eleventh_column_uses_legacy_signature(
    monkeypatch, error, fallback_expected, missing_function
):
    cursor = FakeCursor(error)
    monkeypatch.setattr(connection, "vendor", "postgresql")
    monkeypatch.setattr(connection, "cursor", lambda: cursor)

    repository = CitizenDjangoORMRepository()
    if fallback_expected:
        result = repository.get_internal_user_by_cpf_for_auth("33366699957")
        assert result["mustChangePassword"] is True
        assert len(cursor.queries) == 2
    else:
        expected = FunctionNotFoundError if missing_function else SqlError
        with pytest.raises(expected):
            repository.get_internal_user_by_cpf_for_auth("33366699957")
        assert len(cursor.queries) == 1


def test_safe_atomic_block_rolls_back_when_query_fails():
    exits = []

    class Atomic:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            exits.append(exc_type)
            return False

    with patch("django.db.transaction.atomic", return_value=Atomic()):
        with pytest.raises(SqlError):
            with _safe_atomic_block():
                raise SqlError("permission denied", "42501")

    assert exits == [SqlError]
