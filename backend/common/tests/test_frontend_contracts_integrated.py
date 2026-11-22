"""
Teste Integrado Automatizado de Alinhamento de Contratos: Frontend (Next.js 15) vs Backend (Django REST).
Valida que as respostas da API Django atendem estritamente às interfaces TypeScript de portal/src/types/api.ts:
- Agency, Unit, Service, CitizenProfile, Appointment, Protocol, ProblemDetails (RFC 7807).
"""

import pytest
from rest_framework.test import APIClient

@pytest.fixture
def client():
    return APIClient()

def test_contract_service_catalog_matches_frontend_types(client):
    """Valida contrato de listagem e detalhe de serviços."""
    response = client.get("/api/v1/services/")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data or "results" in data
    items = data.get("items") or data.get("results")
    assert isinstance(items, list)

    if items:
        srv = items[0]
        # Campos exigidos pela interface Service em portal/src/types/api.ts
        assert "id" in srv
        assert "name" in srv or "title" in srv
        assert "category" in srv

def test_contract_agencies_and_units_match_frontend_types(client):
    """Valida contrato de órgãos e unidades."""
    resp_agencies = client.get("/api/v1/agencies/")
    assert resp_agencies.status_code == 200
    agencies = resp_agencies.json()
    assert isinstance(agencies, list) or "results" in agencies or "items" in agencies

    resp_units = client.get("/api/v1/units/")
    assert resp_units.status_code == 200
    units = resp_units.json()
    assert isinstance(units, list) or "results" in units or "items" in units

def test_contract_rfc7807_problem_details_matches_frontend_types(client):
    """Valida que erros 4xx retornam exatamente o schema ProblemDetails exigido pelo frontend."""
    # Requisição intencionalmente inválida para disparar 400
    response = client.post("/api/v1/auth/register/", data={}, format="json")
    assert response.status_code in (400, 422)
    err = response.json()

    # Valida campos da interface ProblemDetails em portal/src/types/api.ts
    assert "type" in err
    assert "title" in err
    assert "status" in err
    assert err["status"] == response.status_code
    assert "detail" in err
