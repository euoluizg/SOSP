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
    """Garante existência de agendamentos de teste para Cidadão B (citizen-002) em duas unidades distintas do mesmo órgão SSP."""
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
    scheduling_repository.save(
        {
            "id": "appt-ssp-tabuleiro",
            "protocolNumber": "20261109-8888",
            "citizenId": "citizen-002",
            "citizenName": "Cidadão B",
            "citizenCpfMasked": "***.333.444-**",
            "serviceId": "servico-emitir-rg",
            "serviceName": "Emitir Carteira de Identidade Nacional (CIN)",
            "agencyId": "orgao-ssp",
            "agencyName": "Secretaria de Estado da Segurança Pública",
            "unitId": "unidade-tabuleiro",
            "unitName": "Central Já! Tabuleiro",
            "unitAddress": "Av. Menino Marcelo, 100 - Tabuleiro dos Martins, Maceió - AL",
            "scheduledDate": "2026-11-15",
            "scheduledTime": "11:30",
            "status": "scheduled",
            "createdAt": "2026-11-09T08:30:00Z",
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


def test_server_cannot_access_appointment_of_another_unit_in_same_agency(server_client):
    """
    Regra Crítica (RN-36 / ADR-003):
    Servidor da unidade-centro NÃO pode acessar agendamento da unidade-tabuleiro,
    mesmo que ambos pertençam ao mesmo órgão (orgao-ssp).
    unit_match or agency_match foi descontinuado: unit_match é estrito.
    """
    # Detalhe do agendamento
    resp_detail = server_client.get("/api/v1/appointments/appt-ssp-tabuleiro")
    assert resp_detail.status_code == 403
    assert resp_detail["Content-Type"] == "application/problem+json"
    assert "outra unidade" in resp_detail.json()["detail"]

    # Consulta por protocolo
    resp_proto = server_client.get("/api/v1/appointments/by-protocol/20261109-8888")
    assert resp_proto.status_code == 403

    # Timeline do protocolo
    resp_time = server_client.get("/api/v1/protocols/20261109-8888/timeline")
    assert resp_time.status_code == 403

    # Tentativa de cancelamento
    resp_cancel = server_client.post(
        "/api/v1/appointments/appt-ssp-tabuleiro/cancel",
        {"reason": "Cancelamento indevido de outra unidade"},
        format="json",
    )
    assert resp_cancel.status_code == 403

    # Tentativa de upload de anexos
    resp_upload = server_client.post(
        "/api/v1/protocols/20261109-8888/documents",
        {"fileName": "anexo.pdf", "sizeMb": 1.0},
        format="json",
    )
    assert resp_upload.status_code == 403


def test_server_tabuleiro_can_access_appointment_in_own_tabuleiro_unit(server_ssp_tabuleiro_client):
    """Servidor lotado na unidade-tabuleiro tem acesso a agendamentos de sua unidade."""
    resp_own = server_ssp_tabuleiro_client.get("/api/v1/appointments/appt-ssp-tabuleiro")
    assert resp_own.status_code == 200
    assert resp_own.json()["unitId"] == "unidade-tabuleiro"

    # Não acessa a unidade-centro (mesmo órgão SSP)
    resp_other = server_ssp_tabuleiro_client.get("/api/v1/appointments/appt-001")
    assert resp_other.status_code == 403


def test_manager_ssp_can_access_all_units_of_own_agency_but_not_other_agencies(manager_ssp_client):
    """Gestor institucional SSP (sem unidade específica) acessa qualquer unidade do órgão SSP, mas não de outros órgãos."""
    # Acessa unidade-centro do seu órgão
    resp_centro = manager_ssp_client.get("/api/v1/appointments/appt-001")
    assert resp_centro.status_code == 200

    # Acessa unidade-tabuleiro do seu órgão
    resp_tabuleiro = manager_ssp_client.get("/api/v1/appointments/appt-ssp-tabuleiro")
    assert resp_tabuleiro.status_code == 200

    # Bloqueado em agendamento de outro órgão (DETRAN)
    resp_detran = manager_ssp_client.get("/api/v1/appointments/appt-002")
    assert resp_detran.status_code == 403


def test_server_citizen_appointments_list_is_strictly_scoped_to_unit(server_client):
    """Servidor da unidade-centro só visualiza agendamentos da unidade-centro na listagem do cidadão."""
    response = server_client.get("/api/v1/citizens/citizen-002/appointments")
    assert response.status_code == 200
    appts = response.json()
    assert len(appts) >= 1
    assert all(a["unitId"] == "unidade-centro" for a in appts)
    # Não pode conter o agendamento de tabuleiro
    assert not any(a["id"] == "appt-ssp-tabuleiro" for a in appts)


def test_server_without_scope_is_blocked_fail_closed(server_without_scope_client):
    """Servidor sem escopo de órgão nem unidade é sumariamente bloqueado (Fail-Closed)."""
    resp_appt = server_without_scope_client.get("/api/v1/appointments/appt-001")
    assert resp_appt.status_code == 403
    assert "sem escopo organizacional" in resp_appt.json()["detail"]

    resp_list = server_without_scope_client.get("/api/v1/citizens/citizen-001/appointments")
    assert resp_list.status_code == 403

    resp_rep = server_without_scope_client.get("/api/v1/reports/appointments")
    assert resp_rep.status_code == 403

    resp_exp = server_without_scope_client.post("/api/v1/reports/exports", {"type": "csv"}, format="json")
    assert resp_exp.status_code == 403


def test_server_without_unit_cannot_access_appointments_fail_closed(server_without_unit_client):
    """Servidor operacional com órgão mas sem unidade não pode acessar agendamentos presenciais (Fail-Closed)."""
    resp_appt = server_without_unit_client.get("/api/v1/appointments/appt-001")
    assert resp_appt.status_code == 403
    assert "sem unidade de atendimento" in resp_appt.json()["detail"]

    resp_list = server_without_unit_client.get("/api/v1/citizens/citizen-001/appointments")
    assert resp_list.status_code == 403


def test_manager_without_agency_is_blocked_fail_closed(manager_without_agency_client):
    """Gestor institucional sem órgão de lotação atribuído é bloqueado (Fail-Closed)."""
    resp_appt = manager_without_agency_client.get("/api/v1/appointments/appt-001")
    assert resp_appt.status_code == 403
    assert "sem órgão de lotação" in resp_appt.json()["detail"]

    resp_list = manager_without_agency_client.get("/api/v1/citizens/citizen-001/appointments")
    assert resp_list.status_code == 403

    resp_rep = manager_without_agency_client.get("/api/v1/reports/appointments")
    assert resp_rep.status_code == 403

    resp_exp = manager_without_agency_client.post("/api/v1/reports/exports", {"type": "csv"}, format="json")
    assert resp_exp.status_code == 403


def test_manager_user_rbac_permissions_compatibility():
    """Valida as classes de permissão RBAC (IsServerUser, IsManagerUser, IsInstitutionalUser) com gestores e servidores."""
    from common.security.permissions import IsServerUser, IsManagerUser, IsInstitutionalUser
    from common.security.authentication import SospUser

    manager = SospUser(user_id="mgr-1", role="gestor", agency_id="orgao-ssp")
    server = SospUser(user_id="srv-1", role="server", unit_id="unidade-centro")
    citizen = SospUser(user_id="cit-1", role="citizen")

    class DummyReq:
        def __init__(self, user):
            self.user = user

    # Gestor
    assert IsServerUser().has_permission(DummyReq(manager), None) is True
    assert IsManagerUser().has_permission(DummyReq(manager), None) is True
    assert IsInstitutionalUser().has_permission(DummyReq(manager), None) is True

    # Servidor
    assert IsServerUser().has_permission(DummyReq(server), None) is True
    assert IsManagerUser().has_permission(DummyReq(server), None) is False  # Servidor não é gestor
    assert IsInstitutionalUser().has_permission(DummyReq(server), None) is True

    # Cidadão
    assert IsServerUser().has_permission(DummyReq(citizen), None) is False
    assert IsManagerUser().has_permission(DummyReq(citizen), None) is False
    assert IsInstitutionalUser().has_permission(DummyReq(citizen), None) is False


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


def test_server_reports_are_strictly_scoped_to_own_unit(server_client):
    """Relatórios acessados por servidor são estritamente restritos à sua unidade/órgão (RN-36)."""
    resp = server_client.get("/api/v1/reports/appointments")
    assert resp.status_code == 200
    data = resp.json()
    assert data["scope"]["unitId"] == "unidade-centro"
    assert data["scope"]["agencyId"] == "orgao-ssp"
    assert all(a.get("unitId") == "unidade-centro" for a in data["recentQueue"])


def test_server_cannot_request_reports_of_another_agency(server_client):
    """Servidor recebe 403 ao tentar solicitar relatório de outro órgão."""
    resp = server_client.get("/api/v1/reports/appointments?agencyId=orgao-detran")
    assert resp.status_code == 403
    assert resp["Content-Type"] == "application/problem+json"


def test_server_cannot_request_reports_of_another_unit_in_same_agency(server_client):
    """Servidor recebe 403 ao tentar solicitar relatório de outra unidade (mesmo do mesmo órgão)."""
    resp = server_client.get("/api/v1/reports/appointments?unitId=unidade-tabuleiro")
    assert resp.status_code == 403
    assert resp["Content-Type"] == "application/problem+json"


def test_server_export_preserves_authenticated_user_identity_and_enforces_scope(server_client):
    """Exportação solicitada por servidor registra sua identidade real e injeta seu escopo de unidade."""
    resp = server_client.post("/api/v1/reports/exports", {"type": "csv"}, format="json")
    assert resp.status_code == 201
    data = resp.json()
    assert data["requestedBy"] == "server-001"
    assert data["filters"]["unitId"] == "unidade-centro"
    assert data["filters"]["agencyId"] == "orgao-ssp"


def test_server_cannot_export_reports_of_another_agency_or_unit(server_client):
    """Servidor é impedido com 403 ao tentar exportar dados de outro órgão ou unidade."""
    resp_agency = server_client.post(
        "/api/v1/reports/exports",
        {"type": "csv", "filters": {"agencyId": "orgao-detran"}},
        format="json",
    )
    assert resp_agency.status_code == 403

    resp_unit = server_client.post(
        "/api/v1/reports/exports",
        {"type": "csv", "filters": {"unitId": "unidade-tabuleiro"}},
        format="json",
    )
    assert resp_unit.status_code == 403


def test_admin_export_records_authenticated_admin_identity(admin_client):
    """Exportação solicitada por administrador registra a identidade real do admin."""
    resp = admin_client.post(
        "/api/v1/reports/exports",
        {"type": "pdf", "filters": {"agencyId": "orgao-detran"}},
        format="json",
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["requestedBy"] == "admin-001"


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
# 6. Conformidade OpenAPI e Tratamento de 405 Method Not Allowed (RFC 9110)
# -------------------------------------------------------------------------


def test_protocol_route_allows_get_for_authorized_owner(auth_client):
    """
    Conforme docs/api/openapi.yaml, GET /protocols/{protocolNumber} é uma rota suportada
    que retorna a linha do tempo do protocolo para o titular autenticado.
    """
    response = auth_client.get("/api/v1/protocols/20261105-1042")
    assert response.status_code == 200
    data = response.json()
    assert data["protocolNumber"] == "20261105-1042"


def test_protocol_route_rejects_unsupported_methods_with_405_and_allow_header(auth_client):
    """
    Conforme RFC 9110 e OpenAPI, métodos não suportados em /protocols/{protocolNumber}
    (ex: POST, PUT, DELETE) devem retornar 405 Method Not Allowed acompanhado do cabeçalho 'Allow'.
    """
    # POST não é permitido
    resp_post = auth_client.post("/api/v1/protocols/20261105-1042", {}, format="json")
    assert resp_post.status_code == 405
    assert resp_post["Content-Type"] == "application/problem+json"
    assert "Allow" in resp_post.headers
    assert "GET" in resp_post.headers["Allow"]
    body_post = resp_post.json()
    assert body_post["status"] == 405
    assert "traceId" in body_post

    # PUT não é permitido
    resp_put = auth_client.put("/api/v1/protocols/20261105-1042", {}, format="json")
    assert resp_put.status_code == 405
    assert "GET" in resp_put.headers.get("Allow", "")

    # DELETE não é permitido
    resp_del = auth_client.delete("/api/v1/protocols/20261105-1042")
    assert resp_del.status_code == 405
    assert "GET" in resp_del.headers.get("Allow", "")


# -------------------------------------------------------------------------
# 7. Regras Legadas de Consulta e CORS
# -------------------------------------------------------------------------


def test_legacy_unscoped_appointment_list_is_not_exposed():
    assert APIClient().get("/api/v1/appointments").status_code == 401


def test_authenticated_legacy_appointment_list_returns_405(auth_client):
    response = auth_client.get("/api/v1/appointments")
    assert response.status_code == 405
    assert response["Content-Type"] == "application/problem+json"
    assert "Allow" in response.headers
    assert "POST" in response.headers["Allow"]


def test_cors_preflight_is_not_blocked_by_authentication(api_client):
    response = api_client.options(
        "/api/v1/appointments",
        HTTP_ORIGIN="http://localhost:3000",
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
    )
    assert response.status_code == 200
    assert response["access-control-allow-origin"] == "http://localhost:3000"
