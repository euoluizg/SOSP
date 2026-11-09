"""Fixtures compartilhadas dos testes do backend SOSP.

O backend opera com política deny-by-default (REST_FRAMEWORK.DEFAULT_PERMISSION_CLASSES
= IsAuthenticated). Endpoints protegidos só podem ser exercitados com um token válido,
por isso os testes usam fixtures autenticadas para os diferentes perfis RBAC do SOSP:
- `auth_client`: cidadão seed (citizen-001) autenticado via endpoint real /auth/login
- `citizen_client_b`: cidadão B (citizen-002) para validações de ownership entre cidadãos
- `server_client`: servidor lotado na unidade-centro
- `server_other_unit_client`: servidor lotado na unidade-farol
- `admin_client`: administrador do sistema
"""

import pytest
from rest_framework.test import APIClient
from common.security.authentication import generate_sosp_token

CITIZEN_SEED_CPF = "11144477705"
CITIZEN_SEED_PASSWORD = "S0sp@2026!Fort3"


@pytest.fixture
def api_client():
    """Cliente DRF anônimo (sem credenciais)."""
    return APIClient()


@pytest.fixture
def auth_client(api_client):
    """Cliente DRF autenticado com token Bearer emitido pelo endpoint de login (cidadão seed citizen-001)."""
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


@pytest.fixture
def citizen_client_b():
    """Cliente DRF autenticado como outro cidadão (citizen-002) para testes de ownership."""
    client = APIClient()
    token = generate_sosp_token(
        user_id="citizen-002",
        role="citizen",
        cpf="22233344455",
        full_name="Cidadão B",
        email="cidadao.b@exemplo.com.br",
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    yield client
    client.credentials()


@pytest.fixture
def server_client():
    """Cliente DRF autenticado como servidor da unidade-centro e órgão SSP."""
    client = APIClient()
    token = generate_sosp_token(
        user_id="server-001",
        role="server",
        agency_id="orgao-ssp",
        unit_id="unidade-centro",
        full_name="Servidor Centro",
        email="servidor.centro@sosp.al.gov.br",
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    yield client
    client.credentials()


@pytest.fixture
def server_other_unit_client():
    """Cliente DRF autenticado como servidor de outra unidade (unidade-farol / DETRAN)."""
    client = APIClient()
    token = generate_sosp_token(
        user_id="server-002",
        role="server",
        agency_id="orgao-detran",
        unit_id="unidade-farol",
        full_name="Servidor Farol",
        email="servidor.farol@sosp.al.gov.br",
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    yield client
    client.credentials()


@pytest.fixture
def admin_client():
    """Cliente DRF autenticado como administrador do sistema."""
    client = APIClient()
    token = generate_sosp_token(
        user_id="admin-001",
        role="admin",
        full_name="Administrador SOSP",
        email="admin@sosp.al.gov.br",
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    yield client
    client.credentials()
