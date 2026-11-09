"""
Testes de enforcement de autorização da API SOSP (RF-01, RF-02, RN-28).

Regra contratual (docs/api/openapi.yaml):
- Operações com `security: [cookieAuth]` exigem autenticação → 401 sem token.
- Operações com `security: []` (ou herança sem esquema global) permanecem públicas.

A política global é deny-by-default (`REST_FRAMEWORK.DEFAULT_PERMISSION_CLASSES`),
com `AllowAny` explícito apenas nos endpoints públicos.
"""

import pytest
from rest_framework.test import APIClient

PROTECTED_ENDPOINTS = [
    ("get", "/api/v1/citizens/me"),
    ("post", "/api/v1/auth/logout"),
    ("get", "/api/v1/citizens/citizen-001/appointments"),
    ("get", "/api/v1/appointments"),
    ("post", "/api/v1/appointments/"),
    ("get", "/api/v1/appointments/appt-001"),
    ("get", "/api/v1/appointments/by-protocol/20261105-1042"),
    ("post", "/api/v1/appointments/appt-001/cancel"),
    ("get", "/api/v1/protocols/20261105-1042"),
    ("post", "/api/v1/protocols/20261105-1042/documents"),
    ("get", "/api/v1/guidance/services/servico-emitir-rg"),
    ("get", "/api/v1/guidance/pdf/job-001"),
    ("post", "/api/v1/questions/"),
    ("post", "/api/v1/feedback/reviews/20261105-1042"),
    ("get", "/api/v1/reports/appointments"),
    ("post", "/api/v1/reports/exports"),
    ("get", "/api/v1/audit/events"),
]

PUBLIC_ENDPOINTS = [
    ("get", "/api/v1/services/"),
    ("get", "/api/v1/services/servico-emitir-rg"),
    ("get", "/api/v1/services/servico-emitir-rg/steps"),
    ("get", "/api/v1/services/servico-emitir-rg/documents"),
    ("get", "/api/v1/agencies/"),
    ("get", "/api/v1/units/"),
    ("get", "/api/v1/units/unidade-centro/slots?date=2026-11-09"),
    ("get", "/api/v1/categories/"),
    ("get", "/api/v1/feedback/faq"),
]


@pytest.mark.parametrize("method,path", PROTECTED_ENDPOINTS)
def test_protected_endpoint_rejects_anonymous(api_client, method, path):
    response = getattr(api_client, method)(path, {}, format="json")
    assert response.status_code == 401, f"{method.upper()} {path} deveria exigir autenticação"


@pytest.mark.parametrize("method,path", PUBLIC_ENDPOINTS)
def test_public_endpoint_allows_anonymous(api_client, method, path):
    response = getattr(api_client, method)(path)
    assert response.status_code == 200, f"{method.upper()} {path} deveria ser público"


def test_health_check_is_public_even_when_database_is_down(api_client):
    """Liveness probe é público. Em ambiente sem banco ele responde 503, nunca 401/403."""
    response = api_client.get("/api/v1/health")
    assert response.status_code in (200, 503)
    assert response.status_code not in (401, 403)
    body = response.json()
    assert body["status"] in ("healthy", "unhealthy")
    assert "database" in body


def test_unauthenticated_response_is_rfc7807_with_www_authenticate(api_client):
    response = api_client.get("/api/v1/citizens/me")
    assert response.status_code == 401
    assert response["Content-Type"] == "application/problem+json"
    assert response["WWW-Authenticate"].lower() == "bearer"
    body = response.json()
    assert body["status"] == 401
    assert body["title"] == "Não autenticado"
    assert "traceId" in body


def test_authenticated_user_can_access_protected_endpoint(auth_client):
    response = auth_client.get("/api/v1/citizens/me")
    assert response.status_code == 200
    assert "cpf" in response.json()


def test_legacy_unscoped_appointment_list_is_not_exposed():
    """GET /appointments não existe no contrato e não pode listar agendamentos de todos."""
    assert APIClient().get("/api/v1/appointments").status_code == 401


def test_authenticated_legacy_appointment_list_returns_405(auth_client):
    """Mesmo autenticado, a listagem irrestrita não é exposta (apenas POST no contrato)."""
    assert auth_client.get("/api/v1/appointments").status_code == 405


def test_cors_preflight_is_not_blocked_by_authentication(api_client):
    response = api_client.options(
        "/api/v1/appointments",
        HTTP_ORIGIN="http://localhost:3000",
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
    )
    assert response.status_code == 200
    assert response["access-control-allow-origin"] == "http://localhost:3000"
