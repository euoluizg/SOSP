"""Regressões da revalidação de identidades institucionais por requisição.

Não usa serviços externos: testa o autenticador real com respostas ORM simuladas.
A suíte PostgreSQL/RLS separada valida os privilégios do banco.
"""
from unittest.mock import patch

import pytest
from django.test import override_settings
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIRequestFactory

from common.security.authentication import SospTokenAuthentication, generate_sosp_token


USER_ID = "f8e88be4-447c-42eb-ac80-35e407f3b5c9"
AGENCY_ID = "b0ed910c-3cc4-4e5a-8ab2-bbe910f40ad2"
UNIT_ID = "1709d5a7-aa66-4b50-8ac2-d2e03a77f6c6"


def _request(role="server", agency_id=AGENCY_ID, unit_id=UNIT_ID):
    token = generate_sosp_token(
        user_id=USER_ID,
        role=role,
        agency_id=agency_id,
        unit_id=unit_id,
        cpf="33366699957",
    )
    return APIRequestFactory().get("/", HTTP_AUTHORIZATION=f"Bearer {token}")


def _current(role="servant", active=True, deleted=None, agency_id=AGENCY_ID, unit_id=UNIT_ID):
    return {
        "role": role,
        "agency_id": agency_id,
        "unit_id": unit_id,
        "is_active": active,
        "deleted_at": deleted,
    }


@pytest.fixture
def authentication_guards():
    with (
        patch("common.security.db_context.set_db_security_context", return_value=True),
        patch("common.security.db_context.clear_db_security_context"),
        patch("apps.accounts.repositories.citizen_repository.is_session_revoked", return_value=False),
    ):
        yield


@pytest.mark.parametrize(
    "record",
    [
        None,
        _current(active=False),
        _current(deleted="2026-11-09T00:00:00Z"),
    ],
)
@override_settings(REPOSITORY_BACKEND="orm")
def test_rejects_deleted_disabled_or_missing_institutional_accounts(authentication_guards, record):
    with patch("apps.accounts.models.InternalUser.objects.filter") as query:
        query.return_value.values.return_value.first.return_value = record
        with pytest.raises(AuthenticationFailed, match="Conta institucional desativada"):
            SospTokenAuthentication().authenticate(_request())


@pytest.mark.parametrize(
    "record",
    [
        _current(role="gestor"),
        _current(agency_id="cccbf611-080e-4430-8ab7-86cf02b72b46"),
        _current(unit_id="3d8791b3-8795-4730-9afb-2398ac2cf4e5"),
        _current(unit_id=None),
    ],
)
@override_settings(REPOSITORY_BACKEND="orm")
def test_rejects_stale_institutional_role_agency_or_unit(authentication_guards, record):
    with patch("apps.accounts.models.InternalUser.objects.filter") as query:
        query.return_value.values.return_value.first.return_value = record
        with pytest.raises(AuthenticationFailed, match="Permissões institucionais alteradas"):
            SospTokenAuthentication().authenticate(_request())


@override_settings(REPOSITORY_BACKEND="orm")
def test_valid_institutional_user_is_allowed(authentication_guards):
    with patch("apps.accounts.models.InternalUser.objects.filter") as query:
        query.return_value.values.return_value.first.return_value = _current()
        user, _ = SospTokenAuthentication().authenticate(_request())
        assert user.role == "server"
        assert str(user.agency_id) == AGENCY_ID
        assert str(user.unit_id) == UNIT_ID


@override_settings(REPOSITORY_BACKEND="orm")
def test_database_failure_during_revalidation_fails_closed(authentication_guards):
    with patch("apps.accounts.models.InternalUser.objects.filter", side_effect=RuntimeError("DB unavailable")):
        with pytest.raises(AuthenticationFailed, match="Falha de segurança ao validar a identidade"):
            SospTokenAuthentication().authenticate(_request())


@override_settings(REPOSITORY_BACKEND="orm")
def test_security_context_initialization_failure_fails_closed():
    with (
        patch("common.security.db_context.set_db_security_context", return_value=False),
        patch("common.security.db_context.clear_db_security_context") as clear_context,
    ):
        with pytest.raises(AuthenticationFailed, match="contexto de segurança"):
            SospTokenAuthentication().authenticate(_request())
        clear_context.assert_called()


@override_settings(REPOSITORY_BACKEND="orm")
def test_citizen_not_found_is_rejected(authentication_guards):
    request = _request(role="citizen", agency_id=None, unit_id=None)
    with patch("apps.accounts.models.Citizen.objects.filter") as query:
        query.return_value.values.return_value.first.return_value = None
        with pytest.raises(AuthenticationFailed, match="Conta desativada"):
            SospTokenAuthentication().authenticate(request)


def test_production_requires_registered_sessions():
    from config.settings import production
    assert production.REQUIRE_REGISTERED_SESSION is True
