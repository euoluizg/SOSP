import pytest
from common.security.authentication import generate_sosp_token


@pytest.fixture
def admin_token():
    return generate_sosp_token(
        user_id="admin-001",
        role="superadmin",
        full_name="Admin SOSP Geral",
        must_change_password=False,
    )


@pytest.fixture
def server_token():
    return generate_sosp_token(
        user_id="server-001",
        role="server",
        agency_id="orgao-ssp",
        unit_id="unidade-centro",
        full_name="João Servidor Central",
        must_change_password=False,
    )


@pytest.fixture
def citizen_token():
    return generate_sosp_token(
        user_id="citizen-001",
        role="citizen",
        full_name="Cidadão Teste",
        must_change_password=False,
    )


def test_search_synonyms_accent_insensitive_and_city_filter(api_client):
    resp = api_client.get("/api/v1/services/?q=tirar%20rg")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert any("Identidade" in item["name"] for item in data["items"])

    resp_city = api_client.get("/api/v1/services/?city=Maceio")
    assert resp_city.status_code == 200
    assert resp_city.json()["total"] >= 1


def test_admin_agency_unit_service_crud_and_soft_delete(api_client, admin_token, citizen_token):
    # Cidadão não pode criar órgão
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {citizen_token}")
    assert api_client.post("/api/v1/agencies", {"name": "Fake", "acronym": "FK", "sphere": "state"}, format="json").status_code == 403

    # Admin cria e desativa órgão
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {admin_token}")
    ag_resp = api_client.post(
        "/api/v1/agencies",
        {"name": "Secretaria de Teste SOSP", "acronym": "STEST", "sphere": "state", "description": "Órgão de teste"},
        format="json",
    )
    assert ag_resp.status_code == 201
    ag_id = ag_resp.json()["id"]
    assert ag_resp.json()["sphere"] == "state"

    # Admin cria unidade e desativa
    un_resp = api_client.post(
        "/api/v1/units",
        {
            "agencyId": ag_id,
            "name": "Central Teste Maceió",
            "cep": "57020-100",
            "street": "Rua Teste",
            "number": "10",
            "neighborhood": "Centro",
            "city": "Maceió",
            "state": "AL",
            "dailyLimit": 50,
        },
        format="json",
    )
    assert un_resp.status_code == 201
    unit_id = un_resp.json()["id"]
    assert un_resp.json()["dailyLimit"] == 50

    # Admin cria serviço e desativa logicamente
    svc_resp = api_client.post(
        "/api/v1/services",
        {
            "name": "Serviço Teste Integrado",
            "category": "Documentos",
            "channel": "inPerson",
            "agencyId": ag_id,
            "description": "Descrição completa do serviço de teste.",
            "isFree": True,
            "averageDeadlineDays": 5,
        },
        format="json",
    )
    assert svc_resp.status_code == 201
    svc_id = svc_resp.json()["id"]
    assert svc_resp.json()["category"] == "Documentos"

    assert api_client.delete(f"/api/v1/services/{svc_id}").status_code == 200
    assert api_client.delete(f"/api/v1/units/{unit_id}").status_code == 200
    assert api_client.delete(f"/api/v1/agencies/{ag_id}").status_code == 200


def test_server_appointments_list_and_status_transition(api_client, server_token):
    fresh_citizen_token = generate_sosp_token(
        user_id="citizen-status-test-001",
        role="citizen",
        full_name="Cidadão Fluxo Servidor",
        must_change_password=False,
    )
    # Cidadão cria agendamento
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {fresh_citizen_token}")
    create_resp = api_client.post(
        "/api/v1/appointments",
        {
            "serviceId": "servico-emitir-rg",
            "unitId": "unidade-centro",
            "scheduledDate": "2026-12-10",
            "scheduledTime": "10:00",
        },
        format="json",
        HTTP_IDEMPOTENCY_KEY="idemp-status-test-001",
    )
    assert create_resp.status_code == 201
    appt_id = create_resp.json()["id"]

    # Cidadão não pode acessar fila operacional institucional
    assert api_client.get("/api/v1/appointments/queue").status_code == 403

    # Servidor lista agendamentos da sua unidade e transiciona status
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {server_token}")
    list_resp = api_client.get("/api/v1/appointments/queue")
    assert list_resp.status_code == 200
    assert any(a["id"] == appt_id for a in list_resp.json())

    call_resp = api_client.patch(
        f"/api/v1/appointments/{appt_id}/status",
        {"status": "in_progress", "note": "Chamado no Guichê 04"},
        format="json",
    )
    assert call_resp.status_code == 200
    assert call_resp.json()["status"] == "confirmed"

    done_resp = api_client.patch(
        f"/api/v1/appointments/{appt_id}/status",
        {"status": "completed", "note": "Concluído"},
        format="json",
    )
    assert done_resp.status_code == 200
    assert done_resp.json()["status"] == "completed"


def test_internal_users_crud_rbac(api_client, admin_token, server_token):
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {server_token}")
    assert api_client.get("/api/v1/internal-users").status_code == 403

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {admin_token}")
    list_resp = api_client.get("/api/v1/internal-users")
    assert list_resp.status_code == 200
    assert isinstance(list_resp.json(), list)

    create_resp = api_client.post(
        "/api/v1/internal-users",
        {
            "fullName": "Maria Atendente Teste",
            "cpf": "12345678909",
            "email": "maria.atendente@sosp.al.gov.br",
            "registrationNumber": "SSP-9901",
            "role": "server",
            "canManageCatalog": False,
        },
        format="json",
    )
    assert create_resp.status_code == 201
    created_id = create_resp.json()["id"]
    assert create_resp.json()["mustChangePassword"] is True

    deact_resp = api_client.delete(f"/api/v1/internal-users/{created_id}")
    assert deact_resp.status_code == 200
    assert deact_resp.json()["isActive"] is False


def test_parse_synonyms_value_handles_postgres_text_and_lists():
    from apps.search.repositories import parse_synonyms_value

    assert parse_synonyms_value('{"identidade","cin","carteira de identidade","rg"}') == [
        "identidade",
        "cin",
        "carteira de identidade",
        "rg",
    ]
    assert parse_synonyms_value('["cnh", "detran"]') == ["cnh", "detran"]
    assert parse_synonyms_value("agua, casal, fatura") == ["agua", "casal", "fatura"]
    assert parse_synonyms_value(["sus", "saude"]) == ["sus", "saude"]
    assert parse_synonyms_value("") == []


@pytest.mark.django_db
def test_orm_appointment_save_survives_protocol_transition_rls_denial(monkeypatch):
    from unittest.mock import patch
    from apps.accounts.models import Citizen, Gender
    from apps.catalog.models import Agency, Service, Unit
    from apps.scheduling.models import Appointment, Protocol, ProtocolTransition
    from apps.scheduling.repositories import SchedulingDjangoORMRepository

    gender, _ = Gender.objects.get_or_create(name="Prefiro não informar", defaults={"sort_order": 4})
    citizen = Citizen.objects.create(
        cpf="52998224725",
        full_name="Luiz Teste Agendamento",
        birth_date="1998-05-10",
        email="luiz.agendamento@exemplo.al.gov.br",
        phone="82999887766",
        password_hash="test_hash_value",
        password_salt="salt",
        gender=gender,
        mother_name="Maria Teste",
        zip_code="57020100",
        street="Rua do Comércio",
        neighborhood="Centro",
        city="Maceió",
        state="AL",
        address_number="123",
    )
    agency = Agency.objects.create(name="SSP Teste", acronym="SSPT", sphere="state", is_active=True)
    unit = Unit.objects.create(
        agency=agency,
        name="Central Já! Teste",
        zip_code="57020100",
        street="Rua do Comércio",
        neighborhood="Centro",
        city="Maceió",
        state="AL",
        address_number="123",
        daily_limit=80,
        is_active=True,
    )
    service = Service.objects.create(
        name="CIN Teste RLS",
        category="documents",
        detailed_description="Teste de agendamento sob RLS",
        eligibility="Todos",
        is_free=True,
        average_deadline_days=10,
        channel="inPerson",
        status="active",
    )

    repo = SchedulingDjangoORMRepository()
    with patch.object(
        ProtocolTransition.objects,
        "create",
        side_effect=PermissionError("new row violates row-level security policy for table schedulingprotocoltransition"),
    ):
        saved = repo.save(
            {
                "id": "appt-legacy-non-uuid",
                "protocolNumber": "20261123-7777",
                "citizenId": str(citizen.id),
                "serviceId": str(service.id),
                "unitId": str(unit.id),
                "scheduledDate": "2026-12-03",
                "scheduledTime": "14:00",
                "status": "scheduled",
            }
        )

    assert saved["protocolNumber"] == "20261123-7777"
    assert Appointment.objects.filter(protocol_number="20261123-7777").exists()
    assert Protocol.objects.filter(protocol_number="20261123-7777").exists()
