"""Fixtures compartilhadas dos testes do backend SOSP.

O backend opera com política deny-by-default (REST_FRAMEWORK.DEFAULT_PERMISSION_CLASSES
= IsAuthenticated). Endpoints protegidos só podem ser exercitados com um token válido,
por isso os testes usam o fixture `auth_client`, que autentica o cidadão seed
(`11144477705`) via fluxo real de login.
"""

import pytest
from rest_framework.test import APIClient

CITIZEN_SEED_CPF = "11144477705"
CITIZEN_SEED_PASSWORD = "S0sp@2026!Fort3"


@pytest.fixture
def api_client():
    """Cliente DRF anônimo (sem credenciais)."""
    return APIClient()


@pytest.fixture
def auth_client(api_client):
    """Cliente DRF autenticado com token Bearer emitido pelo endpoint de login."""
    response = api_client.post(
        "/api/v1/auth/login",
        {"cpf": CITIZEN_SEED_CPF, "password": CITIZEN_SEED_PASSWORD},
        format="json",
    )
    assert response.status_code == 200, response.content
    token = response.json()["token"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    yield api_client
    api_client.credentials()
