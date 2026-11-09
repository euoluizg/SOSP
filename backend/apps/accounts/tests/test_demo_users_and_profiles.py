import pytest
from rest_framework.test import APIClient

@pytest.fixture
def api_client():
    return APIClient()


def test_citizen_demo_login(api_client):
    """Cidadão 1 e Cidadão 2 autenticam com sucesso e recebem perfil citizen."""
    # Cidadão 1
    resp1 = api_client.post("/api/v1/auth/login", {"cpf": "11144477735", "password": "S0sp@2026!Fort3"})
    assert resp1.status_code == 200
    d1 = resp1.json()
    assert d1["citizen"]["role"] == "citizen"
    assert "token" in d1

    # Cidadão 2 (Maria Silva)
    resp2 = api_client.post("/api/v1/auth/login", {"cpf": "22255588846", "password": "S0sp@2026!Fort3"})
    assert resp2.status_code == 200
    d2 = resp2.json()
    assert d2["citizen"]["role"] == "citizen"
    assert d2["citizen"]["fullName"] == "Maria Santos Silva"


def test_server_demo_login(api_client):
    """Servidor Central SSP autentica e recebe papel server com lotação correta."""
    resp = api_client.post("/api/v1/auth/login", {"cpf": "33366699957", "password": "S0sp@2026!Fort3"})
    assert resp.status_code == 200
    d = resp.json()
    assert d["citizen"]["role"] == "server"
    assert d["citizen"]["agencyId"] == "orgao-ssp"
    assert d["citizen"]["unitId"] == "unidade-centro"


def test_manager_demo_login(api_client):
    """Gestor institucional SSP autentica e recebe papel gestor com agência vinculada."""
    resp = api_client.post("/api/v1/auth/login", {"cpf": "55588811194", "password": "S0sp@2026!Fort3"})
    assert resp.status_code == 200
    d = resp.json()
    assert d["citizen"]["role"] == "gestor"
    assert d["citizen"]["agencyId"] == "orgao-ssp"


def test_admin_demo_login(api_client):
    """Superadministrador SOSP autentica e recebe papel superadmin."""
    resp = api_client.post("/api/v1/auth/login", {"cpf": "99988877714", "password": "S0sp@2026!Fort3"})
    assert resp.status_code == 200
    d = resp.json()
    assert d["citizen"]["role"] == "superadmin"


def test_legacy_cpf_alias_support(api_client):
    """Garante compatibilidade retroativa para testes com CPF anterior 11144477705."""
    resp = api_client.post("/api/v1/auth/login", {"cpf": "11144477705", "password": "S0sp@2026!Fort3"})
    assert resp.status_code == 200
    d = resp.json()
    assert d["citizen"]["id"] == "citizen-001"
