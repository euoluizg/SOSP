"""
Testes de enforcement de autorização da API SOSP (Fase 2 — ADR-003, RS-01 a RS-03, RN-35, RN-36).

Cobre exaustivamente:
1. Deny-by-default para anônimos (401 em rotas protegidas).
2. Ownership do Cidadão: cidadão acessa apenas seus próprios agendamentos e protocolos.
3. Anti-enumeração (STRIDE / RS-01): cidadão tentando acessar dados de terceiros recebe 404 Not Found.
4. Conhecimento isolado do protocolo não concede acesso a dados pessoais de terceiros.
5. Escopo de Unidade do Servidor (RN-36): servidor acessa apenas agendamentos de sua unidade de lotação (403 fora do escopo).
6. RBAC Institucional:
   - Relatórios (/reports/*) restritos a servidores e administradores (cidadão recebe 403).
   - Auditoria (/audit/events) restrita exclusivamente a administradores (servidor e cidadão recebem 403).
7. Rota direta /protocols/{protocolNumber} retorna 405 Method Not Allowed.
8. Conformidade com RFC 7807 (ProblemDetails com traceId).
"""

import pytest
from rest_framework.test import APIClient
from apps.scheduling.repositories import scheduling_repository

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


@pytest.fixture(autouse=True)
def setup_test_appointments():
    """Garante existência de agendamento de teste para Cidadão B (citizen-002)."""
    scheduling_repository.save(
        {
            "id": "appt-b-001",
            "protocolNumber": "20261109-7777",
            "citizenId": "citizen-002",
            "citizenName": "Cidadão B",
            "citizenCpfMasked": "***.333.444-**",
            "serviceId": "servico-emitir-rg",
            "serviceName": "Emitir Carteira de Identidade Nacional (CIN)",
            "agencyId": "orgao-ssp",
            "agencyName": "Secretaria de Estado da Segurança Pública",
            "unitId": "unidade-centro",
            "unitName": "Central Já! Centro",
            "unitAddress": "Rua do Comércio, 123 - Centro, Maceió - AL",
            "scheduledDate": "2026-11-12",
            "scheduledTime": "10:00",
            "status": "scheduled",
            "createdAt": "2026-11-09T08:00:00Z",
        }
    )


# -------------------------------------------------------------------------
# 1. Deny-by-default para Usuários Não Autenticados
# -------------------------------------------------------------------------


@pytest.mark.parametrize("method,path", PROTECTED_ENDPOINTS)
def test_protected_endpoint_rejects_anonymous(api_client, method, path):
    response = getattr(api_client, method)(path, {}, format="json")
    assert response.status_code == 401, f"{method.upper()} {path} deveria exigir autenticação"
    assert response["Content-Type"] == "application/problem+json"


@pytest.mark.parametrize("method,path", PUBLIC_ENDPOINTS)
def test_public_endpoint_allows_anonymous(api_client, method, path):
    response = getattr(api_client, method)(path)
    assert response.status_code == 200, f"{method.upper()} {path} deveria ser público"


def test_health_check_is_public_even_when_database_is_down(api_client):
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


# -------------------------------------------------------------------------
# 2. Ownership do Cidadão (Cenários Positivos: Cidadão A nos Próprios Dados)
# -------------------------------------------------------------------------


def test_citizen_a_can_access_own_appointments_list(auth_client):
    """Cidadão A (citizen-001) pode listar seus próprios agendamentos."""
    response = auth_client.get("/api/v1/citizens/citizen-001/appointments")
    assert response.status_code == 200
    appts = response.json()
    assert isinstance(appts, list)
    assert len(appts) >= 1
    assert all(a["citizenId"] == "citizen-001" for a in appts)


def test_citizen_a_can_access_own_appointment_detail(auth_client):
    """Cidadão A pode visualizar detalhes de seu próprio agendamento appt-001."""
    response = auth_client.get("/api/v1/appointments/appt-001")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "appt-001"
    assert data["citizenId"] == "citizen-001"


def test_citizen_a_can_access_own_appointment_by_protocol(auth_client):
    """Cidadão A pode consultar seu agendamento através do protocolo correspondente."""
    response = auth_client.get("/api/v1/appointments/by-protocol/20261105-1042")
    assert response.status_code == 200
    data = response.json()
    assert data["protocolNumber"] == "20261105-1042"
    assert data["citizenId"] == "citizen-001"


def test_citizen_a_can_access_own_protocol_timeline(auth_client):
    """Cidadão A pode consultar a timeline de seu próprio protocolo."""
    response = auth_client.get("/api/v1/protocols/20261105-1042/timeline")
    assert response.status_code == 200
    data = response.json()
    assert data["protocolNumber"] == "20261105-1042"
    assert "stages" in data


# -------------------------------------------------------------------------
# 3. Ownership do Cidadão (Cenários Negativos: Cidadão A Acessando Cidadão B)
# Anti-enumeração (STRIDE / RS-01): Retorna 404 em vez de 403
# -------------------------------------------------------------------------


def test_citizen_a_cannot_list_citizen_b_appointments(auth_client):
    """Cidadão A recebe 404 ao tentar listar agendamentos do Cidadão B (citizen-002)."""
    response = auth_client.get("/api/v1/citizens/citizen-002/appointments")
    assert response.status_code == 404
    assert response["Content-Type"] == "application/problem+json"


def test_citizen_a_cannot_access_citizen_b_appointment_detail(auth_client):
    """Cidadão A recebe 404 ao tentar abrir detalhes de agendamento do Cidadão B (appt-b-001)."""
    response = auth_client.get("/api/v1/appointments/appt-b-001")
    assert response.status_code == 404
    assert response["Content-Type"] == "application/problem+json"


def test_protocol_knowledge_alone_does_not_grant_access_to_third_party_data(auth_client):
    """
    Regra Crítica: O conhecimento isolado do número do protocolo (20261109-7777 do Cidadão B)
    NÃO autoriza o Cidadão A a consultar dados de terceiros → Retorna 404 Not Found.
    """
    response = auth_client.get("/api/v1/appointments/by-protocol/20261109-7777")
    assert response.status_code == 404
    assert response["Content-Type"] == "application/problem+json"


def test_citizen_a_cannot_access_citizen_b_protocol_timeline(auth_client):
    """Cidadão A recebe 404 ao tentar consultar a timeline de protocolo do Cidadão B."""
    response = auth_client.get("/api/v1/protocols/20261109-7777/timeline")
    assert response.status_code == 404
    assert response["Content-Type"] == "application/problem+json"


def test_citizen_a_cannot_upload_documents_to_citizen_b_protocol(auth_client):
    """Cidadão A não pode enviar anexos ao protocolo de terceiro."""
    response = auth_client.post(
        "/api/v1/protocols/20261109-7777/documents",
        {"fileName": "comprovante_indevido.pdf", "sizeMb": 1.0},
        format="json",
    )
    assert response.status_code == 404
    assert response["Content-Type"] == "application/problem+json"


def test_citizen_a_cannot_cancel_citizen_b_appointment(auth_client):
    """Cidadão A não pode cancelar agendamento pertencente ao Cidadão B."""
    response = auth_client.post(
        "/api/v1/appointments/appt-b-001/cancel",
        {"reason": "Tentativa indevida de cancelamento"},
        format="json",
    )
    assert response.status_code == 404
    assert response["Content-Type"] == "application/problem+json"


def test_citizen_b_can_access_own_data(citizen_client_b):
    """Cidadão B (citizen-002) acessa normalmente seu próprio agendamento appt-b-001."""
    resp_detail = citizen_client_b.get("/api/v1/appointments/appt-b-001")
    assert resp_detail.status_code == 200
    assert resp_detail.json()["citizenId"] == "citizen-002"

    resp_proto = citizen_client_b.get("/api/v1/appointments/by-protocol/20261109-7777")
    assert resp_proto.status_code == 200

    resp_time = citizen_client_b.get("/api/v1/protocols/20261109-7777/timeline")
    assert resp_time.status_code == 200


# -------------------------------------------------------------------------
# 4. Escopo Organizacional do Servidor Público (RN-36)
# -------------------------------------------------------------------------


def test_server_can_access_appointment_in_own_unit(server_client):
    """Servidor da unidade-centro pode consultar agendamento appt-001 lotado em sua unidade."""
    response = server_client.get("/api/v1/appointments/appt-001")
    assert response.status_code == 200
    assert response.json()["unitId"] == "unidade-centro"


def test_server_can_access_protocol_in_own_unit(server_client):
    """Servidor da unidade-centro pode consultar protocolo 20261105-1042 de sua unidade."""
    response = server_client.get("/api/v1/appointments/by-protocol/20261105-1042")
    assert response.status_code == 200
    assert response.json()["unitId"] == "unidade-centro"


def test_server_cannot_access_appointment_of_another_unit(server_client):
    """
    Servidor da unidade-centro recebe 403 Forbidden ao tentar acessar appt-002
    (lotado na unidade-farol / DETRAN — RN-36).
    """
    response = server_client.get("/api/v1/appointments/appt-002")
    assert response.status_code == 403
    assert response["Content-Type"] == "application/problem+json"


def test_server_cannot_access_protocol_of_another_unit(server_client):
    """Servidor da unidade-centro recebe 403 ao consultar protocolo da unidade-farol."""
    response = server_client.get("/api/v1/appointments/by-protocol/20261015-8831")
    assert response.status_code == 403
    assert response["Content-Type"] == "application/problem+json"


def test_server_cannot_cancel_appointment_of_another_unit(server_client):
    """Servidor não pode cancelar agendamento de outra unidade."""
    response = server_client.post(
        "/api/v1/appointments/appt-002/cancel",
        {"reason": "Servidor cancelando agendamento fora de sua unidade"},
        format="json",
    )
    assert response.status_code == 403
    assert response["Content-Type"] == "application/problem+json"


def test_server_farol_can_access_appointment_in_farol_unit(server_other_unit_client):
    """Servidor lotado na unidade-farol tem acesso permitido a appt-002."""
    response = server_other_unit_client.get("/api/v1/appointments/appt-002")
    assert response.status_code == 200
    assert response.json()["unitId"] == "unidade-farol"


# -------------------------------------------------------------------------
# 5. RBAC Institucional: Relatórios e Auditoria
# -------------------------------------------------------------------------


def test_citizen_cannot_access_reports(auth_client):
    """Cidadão recebe 403 Forbidden ao tentar acessar relatórios gerenciais."""
    resp_get = auth_client.get("/api/v1/reports/appointments")
    assert resp_get.status_code == 403
    assert resp_get["Content-Type"] == "application/problem+json"

    resp_post = auth_client.post("/api/v1/reports/exports", {"type": "csv"}, format="json")
    assert resp_post.status_code == 403
    assert resp_post["Content-Type"] == "application/problem+json"


def test_server_can_access_reports_but_not_audit(server_client):
    """Servidor público pode acessar relatórios, mas recebe 403 ao tentar ver auditoria."""
    resp_reports = server_client.get("/api/v1/reports/appointments")
    assert resp_reports.status_code == 200

    resp_audit = server_client.get("/api/v1/audit/events")
    assert resp_audit.status_code == 403
    assert resp_audit["Content-Type"] == "application/problem+json"


def test_admin_has_full_administrative_access(admin_client):
    """Administrador acessa relatórios, auditoria e agendamentos de qualquer unidade."""
    resp_reports = admin_client.get("/api/v1/reports/appointments")
    assert resp_reports.status_code == 200

    resp_audit = admin_client.get("/api/v1/audit/events")
    assert resp_audit.status_code == 200

    resp_appt1 = admin_client.get("/api/v1/appointments/appt-001")
    assert resp_appt1.status_code == 200

    resp_appt2 = admin_client.get("/api/v1/appointments/appt-002")
    assert resp_appt2.status_code == 200

    resp_apptb = admin_client.get("/api/v1/appointments/appt-b-001")
    assert resp_apptb.status_code == 200


# -------------------------------------------------------------------------
# 6. Restrição de Rota Direta /protocols/{protocolNumber}
# -------------------------------------------------------------------------


def test_direct_protocol_get_returns_405_method_not_allowed(auth_client):
    """
    Chamada direta a GET /protocols/{protocolNumber} deve retornar 405 Method Not Allowed.
    O endpoint de consulta oficial é /appointments/by-protocol/{protocol} ou timeline.
    """
    response = auth_client.get("/api/v1/protocols/20261105-1042")
    assert response.status_code == 405
    assert response["Content-Type"] == "application/problem+json"
    body = response.json()
    assert body["status"] == 405
    assert "traceId" in body


def test_direct_protocol_post_returns_405(auth_client):
    response = auth_client.post("/api/v1/protocols/20261105-1042", {}, format="json")
    assert response.status_code == 405
    assert response["Content-Type"] == "application/problem+json"


# -------------------------------------------------------------------------
# 7. Regras Legadas de Consulta e CORS
# -------------------------------------------------------------------------


def test_legacy_unscoped_appointment_list_is_not_exposed():
    assert APIClient().get("/api/v1/appointments").status_code == 401


def test_authenticated_legacy_appointment_list_returns_405(auth_client):
    assert auth_client.get("/api/v1/appointments").status_code == 405


def test_cors_preflight_is_not_blocked_by_authentication(api_client):
    response = api_client.options(
        "/api/v1/appointments",
        HTTP_ORIGIN="http://localhost:3000",
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
    )
    assert response.status_code == 200
    assert response["access-control-allow-origin"] == "http://localhost:3000"
