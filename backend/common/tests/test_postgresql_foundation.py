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

from apps.accounts.models import Citizen, Gender, InternalUser
from apps.catalog.models import (
    Agency,
    Unit,
    NonWorkingDay,
    Service,
    ServiceAgency,
    UnitService,
    ServiceStep,
    ServiceDocument,
    Faq,
    ServiceVersion,
    CatalogServiceSearchView,
)
from apps.search.models import QueryLog, Synonym
from apps.guidance.models import GuidanceProgress, GeneratedPdf
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
        assert hasattr(first_view_row, "service_name")
        assert hasattr(first_view_row, "category")
        assert hasattr(first_view_row, "synonyms_list")

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


def test_07_physical_schema_and_all_36_models_alignment():
    """7. Validação física das 36 tabelas e correspondência bidirecional com os 36 Models Django."""
    from django.apps import apps
    from scripts.preflight_schema_inspection import SOSP_EXPECTED_TABLES, SOSP_EXPECTED_VIEWS

    with connection.cursor() as cur:
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
        physical_tables = {r[0].lower() for r in cur.fetchall()}
        assert SOSP_EXPECTED_TABLES.issubset(physical_tables), (
            f"Faltam tabelas físicas do SOSP: {SOSP_EXPECTED_TABLES - physical_tables}"
        )

        cur.execute("SELECT viewname FROM pg_views WHERE schemaname = 'public';")
        physical_views = {r[0].lower() for r in cur.fetchall()}
        assert SOSP_EXPECTED_VIEWS.issubset(physical_views), (
            f"Faltam views físicas do SOSP: {SOSP_EXPECTED_VIEWS - physical_views}"
        )

        cur.execute(
            """
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = 'public';
            """
        )
        pg_cols = {}
        for tname, cname in cur.fetchall():
            pg_cols.setdefault(tname.lower(), set()).add(cname.lower())

    managed_sosp_models = [
        m for m in apps.get_models() if m._meta.managed and m._meta.app_label != "contenttypes"
    ]
    assert len(managed_sosp_models) == 36, f"Esperados 36 models SOSP, encontrados {len(managed_sosp_models)}"

    for model in managed_sosp_models:
        db_table = model._meta.db_table.lower()
        assert db_table in pg_cols, f"Tabela {db_table} do model {model.__name__} não existe no PostgreSQL"
        model_cols = {f.column.lower() for f in model._meta.local_fields}
        # Coluna gerada searchvector em catalogservice é somente leitura no banco
        sql_cols = pg_cols[db_table] - {"searchvector"}
        assert model_cols == sql_cols, (
            f"Divergência de colunas em {model._meta.label} ({db_table}): "
            f"Model={sorted(model_cols)} vs SQL={sorted(sql_cols)}"
        )
        # Executa SELECT real pela ORM em cada uma das 36 tabelas
        list(model.objects.all()[:1])


def test_08_crud_and_relations_on_nine_aligned_models():
    """8. Testes reais de leitura, escrita, relacionamentos e constraints nos 9 models corrigidos."""
    from django.db import IntegrityError

    gender, _ = Gender.objects.get_or_create(name="Masculino", defaults={"sort_order": 1})
    citizen = Citizen.objects.create(
        cpf="99988877766",
        full_name="Cidadão Teste Nove Models",
        email="nove.models@al.gov.br",
        phone="82999991111",
        birth_date=datetime.date(1991, 3, 15),
        gender=gender,
        password_hash="argon2id$v=19$m=65536,t=3,p=4$hash",
        password_salt="salt",
        mother_name="Mãe Teste",
        street="Rua A",
        address_number="10",
        neighborhood="Centro",
        city="Maceió",
        state="AL",
        zip_code="57020000",
    )
    internal_user, _ = InternalUser.objects.get_or_create(
        cpf="12345678901",
        defaults={
            "full_name": "Servidor Teste",
            "email": "servidor.teste@al.gov.br",
            "registration_number": "MAT99001",
            "role": "administrator",
            "can_manage_catalog": True,
            "password_hash": "argon2id$hash",
        },
    )
    agency1 = Agency.objects.create(name="Órgão Teste 1", acronym="OT1", sphere="state", is_active=True)
    agency2 = Agency.objects.create(name="Órgão Teste 2", acronym="OT2", sphere="municipal", is_active=True)
    unit1 = Unit.objects.create(
        agency=agency1,
        name="Unidade Teste 1",
        street="Av 1",
        address_number="100",
        neighborhood="Farol",
        city="Maceió",
        state="AL",
        zip_code="57050000",
        daily_limit=30,
    )
    service1 = Service.objects.create(
        name="Serviço Teste Alinhamento 1",
        detailed_description="Descrição para validação de relacionamentos N:N e versionamento.",
        eligibility="Cidadãos alagoanos.",
        category="documents",
        channel="inPerson",
        is_free=True,
        average_deadline_days=3,
        status="active",
        created_by=internal_user,
    )
    service2 = Service.objects.create(
        name="Serviço Teste Alinhamento 2",
        detailed_description="Segundo serviço para testar chave composta em UnitService.",
        eligibility="Qualquer cidadão.",
        category="health",
        channel="hybrid",
        external_url="https://sosp.al.gov.br/saude",
        is_free=True,
        average_deadline_days=1,
        status="active",
    )

    # 8.1 NonWorkingDay (scope + CHECK constraint chkCatalogNonWorkingDayUnit)
    nwd_national = NonWorkingDay.objects.create(
        unit=None,
        day_date=datetime.date(2099, 1, 1),
        description="Confraternização Universal",
        scope="national",
    )
    nwd_unit = NonWorkingDay.objects.create(
        unit=unit1,
        day_date=datetime.date(2099, 6, 24),
        description="Ponto Facultativo da Unidade",
        scope="unit",
    )
    assert NonWorkingDay.objects.filter(id__in=[nwd_national.id, nwd_unit.id]).count() == 2
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            # Violação de chkCatalogNonWorkingDayUnit: scope='unit' sem unitId
            NonWorkingDay.objects.create(
                unit=None,
                day_date=datetime.date(2099, 7, 1),
                description="Inválido sem unidade",
                scope="unit",
            )

    # 8.2 ServiceAgency (PK composta serviceId + agencyId sem coluna id)
    sa1 = ServiceAgency.objects.create(service=service1, agency=agency1)
    sa2 = ServiceAgency(service=service1, agency=agency2)
    sa2.save()
    linked_agencies = list(
        ServiceAgency.objects.filter(service=service1).select_related("agency").values_list("agency__acronym", flat=True)
    )
    assert sorted(linked_agencies) == ["OT1", "OT2"]
    sa1.delete()
    assert ServiceAgency.objects.filter(service=service1).count() == 1
    assert ServiceAgency.objects.filter(service=service1, agency=agency2).exists()

    # 8.3 UnitService (PK composta unitId + serviceId + atualização de is_active)
    us1 = UnitService.objects.create(unit=unit1, service=service1, is_active=True)
    us2 = UnitService.objects.create(unit=unit1, service=service2, is_active=True)
    assert UnitService.objects.filter(unit=unit1).count() == 2
    us1.is_active = False
    us1.save()
    assert UnitService.objects.get(unit=unit1, service=service1).is_active is False
    assert UnitService.objects.get(unit=unit1, service=service2).is_active is True
    us1.delete()
    assert UnitService.objects.filter(unit=unit1).count() == 1

    # 8.4 Faq (sem sortOrder + CHECK constraint chkCatalogFaqLink)
    faq = Faq.objects.create(
        question="Como agendar atendimento presencial?",
        answer="Selecione o serviço, a unidade e o horário disponível.",
        service=service1,
        category="documents",
        is_active=True,
    )
    assert Faq.objects.filter(id=faq.id, service=service1).exists()
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            # Violação de chkCatalogFaqLink: service=None e category=None
            Faq.objects.create(question="Sem vínculo?", answer="Erro", service=None, category=None)

    # 8.5 ServiceVersion (sem changeSummary/approvedBy/approvedAt + FK created_by + UNIQUE)
    sv1 = ServiceVersion.objects.create(
        service=service1,
        version=1,
        snapshot={"name": service1.name, "version": 1},
        created_by=internal_user,
    )
    sv2 = ServiceVersion.objects.create(
        service=service1,
        version=2,
        snapshot={"name": service1.name, "version": 2},
        created_by=None,
    )
    assert service1.versions.count() == 2
    assert sv1.created_by == internal_user
    assert sv2.created_by is None
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            # Violação de uqCatalogServiceVersion (serviceId, version)
            ServiceVersion.objects.create(service=service1, version=1, snapshot={})

    # 8.6 QueryLog (com session_hash + CHECK chkSearchQueryLogCount)
    qlog = QueryLog.objects.create(
        term="segunda via rg",
        filters={"category": "documents"},
        result_count=3,
        session_hash="a" * 64,
    )
    assert QueryLog.objects.get(id=qlog.id).session_hash == "a" * 64
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            QueryLog.objects.create(term="invalido", filters={}, result_count=-1)

    # 8.7 Synonym (sem updatedAt/deletedAt + UNIQUE term + CHECK cardinality > 0)
    syn_term = f"identidade_{uuid.uuid4().hex[:8]}"
    syn = Synonym.objects.create(term=syn_term, synonyms=["rg", "carteira de identidade"], is_active=True)
    assert Synonym.objects.get(id=syn.id).synonyms == ["rg", "carteira de identidade"]
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Synonym.objects.create(term=f"vazio_{uuid.uuid4().hex[:6]}", synonyms=[], is_active=True)

    # 8.8 GuidanceProgress (com started_at, completed_at, updated_at + UNIQUE citizen/service)
    doc = ServiceDocument.objects.create(service=service1, name="Doc Teste: CPF", is_mandatory=True)
    now_ts = timezone.now()
    gp = GuidanceProgress.objects.create(
        citizen=citizen,
        service=service1,
        checked_document_ids=[doc.id],
        completed_at=now_ts,
    )
    gp.refresh_from_db()
    assert gp.started_at is not None
    assert gp.completed_at is not None
    assert gp.checked_document_ids == [doc.id]

    # 8.9 GeneratedPdf (com checklist_hash obrigatório)
    gpdf = GeneratedPdf.objects.create(
        citizen=citizen,
        service=service1,
        file_url="https://sosp.al.gov.br/pdfs/guia-teste.pdf",
        checklist_hash="b" * 64,
        expires_at=now_ts + datetime.timedelta(days=1),
    )
    assert GeneratedPdf.objects.get(id=gpdf.id).checklist_hash == "b" * 64

    # Limpeza controlada dos objetos auxiliares criados neste teste
    gpdf.delete()
    gp.delete()
    syn.delete()
    qlog.delete()
    sv1.delete()
    sv2.delete()
    faq.delete()
    nwd_national.delete()
    nwd_unit.delete()
    internal_user.delete()


def test_09_full_text_search_sosp_portuguese_and_trigram():
    """9. Valida busca textual (sospPortuguese + unaccent + searchVector) e trigram (pg_trgm)."""
    srv = Service.objects.create(
        name="Serviço Teste Emissão de Certidão Negativa de Débitos",
        detailed_description="Orientação completa para regularização tributária e fiscal.",
        eligibility="Contribuintes estaduais e cidadãos.",
        category="taxes",
        channel="inPerson",
        is_free=True,
        average_deadline_days=2,
        status="active",
    )
    with connection.cursor() as cur:
        # Consulta sem acentos e no singular usando plainto_tsquery('sospPortuguese', ...)
        cur.execute(
            """
            SELECT id
            FROM catalogservice
            WHERE id = %s
              AND searchvector @@ plainto_tsquery('public.sospportuguese', 'servico emissao certidao debito tributaria fiscal');
            """,
            [srv.id],
        )
        matched = cur.fetchone()
        assert matched is not None and matched[0] == srv.id

        # Consulta por similaridade trigram (pg_trgm)
        cur.execute(
            """
            SELECT similarity(name, 'Emissao Certidao Negativa')
            FROM catalogservice
            WHERE id = %s;
            """,
            [srv.id],
        )
        sim_score = cur.fetchone()[0]
        assert sim_score > 0.3


def test_10_views_security_invoker_and_rls_enabled():
    """10. Valida metadados de segurança: security_invoker=true nas 2 views e RLS ativo nas 36 tabelas."""
    agency = Agency.objects.create(name="Órgão Teste View", acronym="OTV", sphere="state", is_active=True)
    unit = Unit.objects.create(
        agency=agency,
        name="Unidade Teste View",
        street="Rua V",
        address_number="1",
        neighborhood="Centro",
        city="Maceió",
        state="AL",
        zip_code="57000000",
        daily_limit=20,
        is_active=True,
    )
    service = Service.objects.create(
        name="Serviço Teste View",
        detailed_description="Descrição para view de busca.",
        eligibility="Todos.",
        category="documents",
        channel="inPerson",
        is_free=True,
        average_deadline_days=1,
        status="active",
    )
    ServiceAgency.objects.create(service=service, agency=agency)
    Slot.objects.create(
        unit=unit,
        slot_date=datetime.date(2099, 11, 20),
        starts_at=datetime.time(8, 0),
        ends_at=datetime.time(8, 30),
        capacity=3,
        booked_count=1,
    )

    view_srv = CatalogServiceSearchView.objects.filter(service_id=service.id).first()
    assert view_srv is not None
    assert view_srv.service_name == "Serviço Teste View"
    assert view_srv.agency_acronym == "OTV"

    view_slot = SlotAvailabilityView.objects.filter(unit_id=unit.id, slot_date=datetime.date(2099, 11, 20)).first()
    assert view_slot is not None
    assert view_slot.available_slots == 2
    assert view_slot.is_available is True

    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT c.relname, c.reloptions
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relkind = 'v'
            ORDER BY c.relname;
            """
        )
        views = dict(cur.fetchall())
        assert "vw_catalogservicesearch" in views
        assert "vw_schedulingslotavailability" in views
        assert views["vw_catalogservicesearch"] and "security_invoker=true" in views["vw_catalogservicesearch"]
        assert views["vw_schedulingslotavailability"] and "security_invoker=true" in views["vw_schedulingslotavailability"]

        cur.execute(
            """
            SELECT count(*)
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relkind = 'r' AND c.relrowsecurity = true;
            """
        )
        rls_enabled_count = cur.fetchone()[0]
        assert rls_enabled_count == 36, f"Esperadas 36 tabelas com RLS ativo, encontradas {rls_enabled_count}"

