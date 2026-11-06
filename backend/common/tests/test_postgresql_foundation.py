"""
Testes automatizados da base definitiva Django ORM + PostgreSQL (Etapa 3 / ADR-001 / ADR-002).

Valida:
1. Conexão real com PostgreSQL e extensões.
2. Inserção e recuperação de dados via Models em accounts, catalog e scheduling.
3. Repositórios em modo ORM (REPOSITORY_BACKEND=orm).
4. Concorrência atômica com select_for_update() na reserva de vagas (RN-18).
5. Consulta através das Views unmanaged (vw_catalogservicesearch e vw_schedulingslotavailability).
6. Transação atômica e rollback em caso de erro.
7. Compatibilidade com pytest e isolamento de banco.
"""

import uuid
import datetime
import threading
import pytest
from django.db import connection, transaction
from django.conf import settings
from django.utils import timezone

from apps.accounts.models import Citizen, Gender
from apps.catalog.models import (
    Agency,
    Unit,
    Service,
    ServiceStep,
    ServiceDocument,
    CatalogServiceSearchView,
)
from apps.scheduling.models import Slot, Appointment, Protocol, SlotAvailabilityView
from apps.catalog.repositories import CatalogDjangoORMRepository
from apps.accounts.repositories import CitizenDjangoORMRepository
from apps.scheduling.repositories import SchedulingDjangoORMRepository
from common.exceptions import ProblemDetailsException

pytestmark = [
    pytest.mark.django_db(transaction=True),
    pytest.mark.skipif(
        connection.vendor != "postgresql",
        reason="Estes testes requerem conexão com banco PostgreSQL real com schema baseline aplicado.",
    ),
]


@pytest.fixture(autouse=True)
def setup_teardown_data():
    """Garante isolamento dos dados de teste criados neste módulo."""
    yield
    # Limpeza reversa em ordem de FK para não deixar lixo no banco
    if connection.vendor == "postgresql":
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM schedulingprotocolattachment WHERE filename LIKE 'test_%';")
            cursor.execute("DELETE FROM schedulingprotocol WHERE protocolnumber LIKE '2099%' OR protocolnumber LIKE 'TEST-%';")
            cursor.execute("DELETE FROM schedulingappointment WHERE protocolnumber LIKE '2099%' OR protocolnumber LIKE 'TEST-%';")
            cursor.execute("DELETE FROM schedulingslot WHERE slotdate >= '2099-01-01';")
            cursor.execute("DELETE FROM catalogservicedocument WHERE name LIKE 'Doc Teste%';")
            cursor.execute("DELETE FROM catalogservicestep WHERE title LIKE 'Etapa Teste%';")
            cursor.execute("DELETE FROM catalogserviceagency WHERE serviceid IN (SELECT id FROM catalogservice WHERE name LIKE 'Serviço Teste%');")
            cursor.execute("DELETE FROM catalogunitservice WHERE serviceid IN (SELECT id FROM catalogservice WHERE name LIKE 'Serviço Teste%');")
            cursor.execute("DELETE FROM catalogservice WHERE name LIKE 'Serviço Teste%';")
            cursor.execute("DELETE FROM catalogunit WHERE name LIKE 'Unidade Teste%';")
            cursor.execute("DELETE FROM catalogagency WHERE name LIKE 'Órgão Teste%';")
            cursor.execute("DELETE FROM accountscitizen WHERE cpf IN ('99988877766', '88877766655', '77766655544');")


def test_01_postgresql_real_connection():
    """1. Valida conexão ativa com PostgreSQL e presença de extensões."""
    assert connection.vendor == "postgresql", "A conexão ativa deve ser PostgreSQL"
    with connection.cursor() as cursor:
        cursor.execute("SELECT version();")
        version_str = cursor.fetchone()[0]
        assert "PostgreSQL" in version_str

        # Verifica extensões pg_trgm e unaccent exigidas no schema
        cursor.execute("SELECT extname FROM pg_extension WHERE extname IN ('unaccent', 'pg_trgm');")
        extensions = {row[0] for row in cursor.fetchall()}
        assert "unaccent" in extensions, "Extensão 'unaccent' deve estar ativa"
        assert "pg_trgm" in extensions, "Extensão 'pg_trgm' deve estar ativa"


def test_02_models_crud_accounts_catalog_scheduling():
    """2. Inserção e recuperação de dados via Models nos 3 módulos críticos."""
    # ACCOUNTS: Citizen
    gender, _ = Gender.objects.get_or_create(name="Masculino", defaults={"sort_order": 1})
    citizen = Citizen.objects.create(
        cpf="99988877766",
        full_name="Cidadão Teste ORM",
        email="cidadao.teste@al.gov.br",
        phone="82999990000",
        birth_date=datetime.date(1990, 5, 20),
        gender=gender,
        password_hash="argon2id$v=19$m=65536,t=3,p=4$dummyhash",
        password_salt="dummysalt123456",
        mother_name="Maria dos Santos",
        street="Rua dos Testes",
        address_number="100",
        neighborhood="Centro",
        city="Maceió",
        state="AL",
        zip_code="57020000",
        is_active=True,
    )
    assert citizen.id is not None
    fetched_citizen = Citizen.objects.get(cpf="99988877766")
    assert fetched_citizen.full_name == "Cidadão Teste ORM"
    assert fetched_citizen.city == "Maceió"

    # CATALOG: Agency, Unit, Service, Steps, Documents
    agency = Agency.objects.create(
        name="Órgão Teste ORM",
        acronym="OTORM",
        sphere="state",
        description="Órgão criado para validação do ORM",
        is_active=True,
    )
    unit = Unit.objects.create(
        agency=agency,
        name="Unidade Teste Central",
        street="Av Central",
        address_number="50",
        neighborhood="Farol",
        city="Maceió",
        state="AL",
        zip_code="57050000",
        daily_limit=50,
        is_active=True,
    )
    service = Service.objects.create(
        name="Serviço Teste Licenciamento",
        detailed_description="Descrição detalhada do serviço de licenciamento para teste ORM.",
        category="transport",
        channel="inPerson",
        is_free=True,
        average_deadline_days=5,
        status="active",
    )
    step1 = ServiceStep.objects.create(
        service=service,
        step_order=1,
        title="Etapa Teste 1: Documentação",
        description="Apresentar documentos originais.",
    )
    doc1 = ServiceDocument.objects.create(
        service=service,
        name="Doc Teste: CRLV",
        template_url="https://sosp.al.gov.br/templates/crlv.pdf",
        is_mandatory=True,
    )

    # Verifica integridade referencial do catálogo
    assert service.steps.count() == 1
    assert service.documents.count() == 1
    assert service.steps.first().title == "Etapa Teste 1: Documentação"

    # SCHEDULING: Slot, Appointment, Protocol
    slot = Slot.objects.create(
        unit=unit,
        slot_date=datetime.date(2099, 12, 1),
        starts_at=datetime.time(9, 0),
        ends_at=datetime.time(9, 30),
        capacity=2,
        booked_count=0,
    )
    protocol_num = "20991201-0001"
    appt = Appointment.objects.create(
        protocol_number=protocol_num,
        citizen=citizen,
        service=service,
        unit=unit,
        slot=slot,
        scheduled_date=datetime.date(2099, 12, 1),
        scheduled_time=datetime.time(9, 0),
        status="scheduled",
    )
    protocol = Protocol.objects.create(
        protocol_number=protocol_num,
        protocol_type="appointment",
        citizen=citizen,
        appointment=appt,
        status="received",
    )
    assert appt.id is not None
    assert protocol.id is not None

    fetched_appt = Appointment.objects.select_related("citizen", "service", "unit").get(protocol_number=protocol_num)
    assert fetched_appt.citizen.full_name == "Cidadão Teste ORM"
    assert fetched_appt.service.name == "Serviço Teste Licenciamento"
    assert fetched_appt.unit.name == "Unidade Teste Central"


def test_03_repositories_in_orm_mode():
    """3. Teste dos repositórios quando REPOSITORY_BACKEND=orm."""
    # Prepara entidades base
    agency = Agency.objects.create(name="Órgão Teste Repos", acronym="OTR", sphere="state", is_active=True)
    unit = Unit.objects.create(
        agency=agency,
        name="Unidade Teste Repos",
        street="Rua R",
        address_number="1",
        neighborhood="N",
        city="Maceió",
        state="AL",
        zip_code="57000000",
        daily_limit=20,
        is_active=True,
    )
    service = Service.objects.create(
        name="Serviço Teste Repositório",
        detailed_description="Serviço para validar CatalogDjangoORMRepository.",
        category="work",
        channel="inPerson",
        is_free=True,
        average_deadline_days=2,
        status="active",
    )
    gender, _ = Gender.objects.get_or_create(name="Feminino", defaults={"sort_order": 2})
    citizen = Citizen.objects.create(
        cpf="88877766655",
        full_name="Cidadã Teste Repositório",
        email="cidada.repos@al.gov.br",
        phone="82988880000",
        birth_date=datetime.date(1992, 8, 10),
        gender=gender,
        password_hash="dummyhash",
        password_salt="dummysalt",
        mother_name="Maria Repos",
        street="Rua Cidadã",
        address_number="2",
        neighborhood="Bairro",
        city="Arapiraca",
        state="AL",
        zip_code="57300000",
        is_active=True,
    )

    # 3.1 Catalog Repository
    cat_repo = CatalogDjangoORMRepository()
    agencies = cat_repo.get_agencies()
    assert any(a["id"] == str(agency.id) for a in agencies)
    agency_dict = cat_repo.get_agency_by_id(str(agency.id))
    assert agency_dict is not None and agency_dict["acronym"] == "OTR"

    units = cat_repo.get_units(agency_id=str(agency.id))
    assert len(units) >= 1
    assert units[0]["name"] == "Unidade Teste Repos"

    services = cat_repo.get_services()
    assert any(s["id"] == str(service.id) for s in services)
    srv_dict = cat_repo.get_service_by_id(str(service.id))
    assert srv_dict is not None and srv_dict["name"] == "Serviço Teste Repositório"

    # 3.2 Citizen Repository
    cit_repo = CitizenDjangoORMRepository()
    by_cpf = cit_repo.get_by_cpf("88877766655")
    assert by_cpf is not None
    assert by_cpf["fullName"] == "Cidadã Teste Repositório"
    by_id = cit_repo.get_by_id(str(citizen.id))
    assert by_id is not None
    assert by_id["cpf"] == "88877766655"

    # 3.3 Scheduling Repository
    sched_repo = SchedulingDjangoORMRepository()
    slot = Slot.objects.create(
        unit=unit,
        slot_date=datetime.date(2099, 12, 10),
        starts_at=datetime.time(10, 0),
        ends_at=datetime.time(10, 30),
        capacity=5,
        booked_count=0,
    )
    appt_data = {
        "id": None,
        "protocolNumber": "20991210-9999",
        "citizenId": str(citizen.id),
        "serviceId": str(service.id),
        "unitId": str(unit.id),
        "scheduledDate": datetime.date(2099, 12, 10),
        "scheduledTime": datetime.time(10, 0),
        "status": "scheduled",
        "idempotencyKey": "idemp-test-repo-001",
    }
    saved_appt = sched_repo.save(appt_data)
    assert saved_appt["protocolNumber"] == "20991210-9999"

    retrieved = sched_repo.get_by_protocol("20991210-9999")
    assert retrieved is not None
    assert retrieved["citizenName"] == "Cidadã Teste Repositório"


def test_04_concurrency_select_for_update():
    """4. Teste de concorrência atômica com select_for_update() em Slot (RN-18).
    
    Cria um slot com capacidade = 1 e booked_count = 0.
    Dispara duas threads simultâneas tentando ocupar a última vaga.
    Comprova que apenas uma sucede e a outra recebe erro de vaga esgotada (HTTP 409).
    """
    agency = Agency.objects.create(name="Órgão Teste Lock", acronym="OTL", sphere="state", is_active=True)
    unit = Unit.objects.create(
        agency=agency,
        name="Unidade Teste Lock",
        street="Rua L",
        address_number="10",
        neighborhood="Centro",
        city="Maceió",
        state="AL",
        zip_code="57000000",
        daily_limit=10,
        is_active=True,
    )
    service = Service.objects.create(
        name="Serviço Teste Concorrência",
        detailed_description="Serviço para testar concorrência de slots.",
        category="health",
        channel="inPerson",
        status="active",
    )
    gender, _ = Gender.objects.get_or_create(name="Masculino", defaults={"sort_order": 1})
    citizen1 = Citizen.objects.create(
        cpf="77766655544",
        full_name="Cidadão Lock 1",
        email="lock1@al.gov.br",
        phone="82977770000",
        birth_date=datetime.date(1985, 1, 1),
        gender=gender,
        password_hash="dummyhash",
        password_salt="dummysalt",
        mother_name="Maria Lock",
        street="Rua 1",
        address_number="1",
        neighborhood="N",
        city="Maceió",
        state="AL",
        zip_code="57000000",
        is_active=True,
    )

    # Slot com EXATAMENTE 1 vaga
    slot_date = datetime.date(2099, 12, 15)
    slot_time = datetime.time(14, 0)
    slot = Slot.objects.create(
        unit=unit,
        slot_date=slot_date,
        starts_at=slot_time,
        ends_at=datetime.time(14, 30),
        capacity=1,
        booked_count=0,
    )

    sched_repo = SchedulingDjangoORMRepository()
    results = []
    errors = []

    def attempt_booking(worker_id: int):
        # Cada thread abre uma conexão isolada com o PostgreSQL
        from django.db import connections
        connections.close_all()
        try:
            data = {
                "id": None,
                "protocolNumber": f"20991215-000{worker_id}",
                "citizenId": str(citizen1.id),
                "serviceId": str(service.id),
                "unitId": str(unit.id),
                "scheduledDate": slot_date,
                "scheduledTime": slot_time,
                "status": "scheduled",
                "idempotencyKey": f"idemp-lock-worker-{worker_id}",
            }
            res = sched_repo.save(data)
            results.append((worker_id, res))
        except Exception as exc:
            errors.append((worker_id, exc))
        finally:
            connections.close_all()

    # Cria e dispara 2 threads simultaneamente
    t1 = threading.Thread(target=attempt_booking, args=(1,))
    t2 = threading.Thread(target=attempt_booking, args=(2,))

    t1.start()
    t2.start()

    t1.join(timeout=10)
    t2.join(timeout=10)

    # Uma thread deve ter obtido sucesso
    assert len(results) == 1, f"Exatamente uma requisição deve vencer a concorrência. Resultados: {results}, Erros: {errors}"
    # A outra thread deve ter falhado com ProblemDetailsException (409 Vaga Esgotada)
    assert len(errors) == 1, f"Exatamente uma requisição deve falhar. Erros: {errors}"
    failed_error = errors[0][1]
    assert isinstance(failed_error, ProblemDetailsException)
    assert failed_error.status_code == 409
    assert "Não há vagas disponíveis" in failed_error.detail

    # Verifica o estado final do slot no banco
    slot.refresh_from_db()
    assert slot.booked_count == 1, "O contador de vagas ocupadas deve ser exatamente 1"


def test_05_unmanaged_views_querying():
    """5. Consulta através das Views unmanaged pelo Django ORM."""
    # 5.1 vw_catalogservicesearch
    search_qs = CatalogServiceSearchView.objects.all()
    # A view deve ser consultável sem erro SQL
    total_services_in_view = search_qs.count()
    assert total_services_in_view >= 0

    first_view_row = search_qs.first()
    if first_view_row:
        assert hasattr(first_view_row, "name")
        assert hasattr(first_view_row, "category")
        assert hasattr(first_view_row, "document_names")
        assert hasattr(first_view_row, "document_count")

    # 5.2 vw_schedulingslotavailability
    slot_view_qs = SlotAvailabilityView.objects.all()
    total_slots_in_view = slot_view_qs.count()
    assert total_slots_in_view >= 0

    first_slot_view = slot_view_qs.first()
    if first_slot_view:
        assert hasattr(first_slot_view, "slot_date")
        assert hasattr(first_slot_view, "available_slots")
        assert hasattr(first_slot_view, "unit_name")


def test_06_atomic_transaction_and_rollback():
    """6. Transação atômica e rollback em caso de falha."""
    agency_count_before = Agency.objects.count()

    with pytest.raises(RuntimeError):
        with transaction.atomic():
            Agency.objects.create(
                name="Órgão Rollback Teste",
                acronym="ORT",
                sphere="state",
                is_active=True,
            )
            # Simula falha catastrófica no meio da transação
            raise RuntimeError("Erro forçado para disparar ROLLBACK")

    agency_count_after = Agency.objects.count()
    assert agency_count_after == agency_count_before, "O registro deve ter sido desfeito pelo ROLLBACK"
    assert not Agency.objects.filter(acronym="ORT").exists()
