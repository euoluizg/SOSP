import pytest
from rest_framework.test import APIClient
from common.security.authentication import generate_sosp_token

@pytest.fixture(autouse=True)
def reset_agency_state():
    """Restaura o estado do órgão SSP após cada teste para evitar contaminação entre testes."""
    from apps.catalog.repositories import catalog_repository
    original = catalog_repository.get_agency_by_id("orgao-ssp")
    orig_copy = dict(original) if original else None
    yield
    if orig_copy:
        catalog_repository.update_agency("orgao-ssp", orig_copy)

@pytest.fixture
def admin_token():
    return generate_sosp_token(
        user_id="admin-001",
        role="superadmin",
        full_name="Admin SOSP Geral",
    )

@pytest.fixture
def ssp_manager_token():
    return generate_sosp_token(
        user_id="manager-001",
        role="gestor",
        agency_id="orgao-ssp",
        full_name="Carlos Gestor SSP",
    )

@pytest.fixture
def detran_manager_token():
    return generate_sosp_token(
        user_id="manager-002",
        role="gestor",
        agency_id="orgao-detran",
        full_name="Gestor Detran",
    )

@pytest.fixture
def citizen_token():
    return generate_sosp_token(
        user_id="citizen-001",
        role="citizen",
        full_name="Cidadão Teste",
    )


def test_get_agency_detail_public(api_client):
    """Qualquer usuário pode consultar detalhes de um órgão existente."""
    resp = api_client.get("/api/v1/agencies/orgao-ssp")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "orgao-ssp"
    assert data["acronym"] == "SSP"


def test_get_agency_not_found(api_client):
    """Consulta a órgão inexistente retorna 404 RFC 7807."""
    resp = api_client.get("/api/v1/agencies/orgao-inexistente-xyz")
    assert resp.status_code == 404
    data = resp.json()
    assert data["status"] == 404


def test_patch_agency_by_admin_success(api_client, admin_token):
    """Superadministrador pode editar dados de qualquer órgão."""
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {admin_token}")
    payload = {
        "name": "Secretaria de Segurança Pública de Alagoas (Atualizada)",
        "description": "Nova descrição oficial atualizada pelo administrador geral.",
    }
    resp = api_client.patch("/api/v1/agencies/orgao-ssp", payload, format="json")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "orgao-ssp"
    assert data["name"] == "Secretaria de Segurança Pública de Alagoas (Atualizada)"
    assert data["description"] == "Nova descrição oficial atualizada pelo administrador geral."


def test_patch_agency_by_authorized_manager_success(api_client, ssp_manager_token):
    """Gestor institucional pode editar o órgão de sua lotação."""
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {ssp_manager_token}")
    payload = {
        "acronym": "SSP-AL",
        "description": "Atualização pelo gestor responsável da SSP.",
    }
    resp = api_client.patch("/api/v1/agencies/orgao-ssp", payload, format="json")
    assert resp.status_code == 200
    data = resp.json()
    assert data["acronym"] == "SSP-AL"


def test_patch_agency_by_unauthorized_manager_forbidden(api_client, detran_manager_token):
    """Gestor do DETRAN não pode editar a SSP (403 Forbidden)."""
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {detran_manager_token}")
    payload = {"name": "Tentativa de alteração não autorizada"}
    resp = api_client.patch("/api/v1/agencies/orgao-ssp", payload, format="json")
    assert resp.status_code == 403
    data = resp.json()
    assert data["status"] == 403
    assert "fora de sua instituição" in data["detail"]


def test_patch_agency_by_citizen_forbidden(api_client, citizen_token):
    """Cidadão não possui permissão de gestor e recebe 403."""
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {citizen_token}")
    resp = api_client.patch("/api/v1/agencies/orgao-ssp", {"name": "Hacked"}, format="json")
    assert resp.status_code == 403


def test_patch_agency_anonymous_unauthorized(api_client):
    """Usuário anônimo sem credenciais recebe 401 Unauthorized."""
    resp = api_client.patch("/api/v1/agencies/orgao-ssp", {"name": "Anon"}, format="json")
    assert resp.status_code == 401


def test_patch_agency_invalid_data_rfc7807(api_client, admin_token):
    """Tentativa de enviar nome vazio retorna 400 com formato RFC 7807."""
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {admin_token}")
    resp = api_client.patch("/api/v1/agencies/orgao-ssp", {"name": "  "}, format="json")
    assert resp.status_code == 400
    data = resp.json()
    assert data["status"] == 400
    assert "errors" in data or "detail" in data
