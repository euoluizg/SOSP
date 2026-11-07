"""
Testes de Regressão e Homologação dos Riscos da Etapa 4C.1.1 (PR #14):
1. Migração SQLite não-destrutiva preservando dados e relacionamentos pré-existentes nas 9 tabelas,
   além da inicialização limpa de um SQLite vazio.
2. Semântica segura de chaves primárias compostas (CompositeKeyForeignKey, CompositeKeyModel,
   CompositeKeyQuerySet) em ServiceAgency e UnitService com múltiplas associações compartilhando
   a primeira coluna.
3. Garantia de no-op físico das migrations 0002 em PostgreSQL.
"""
import datetime
import importlib
import uuid
from unittest.mock import MagicMock

import pytest
from django.conf import settings
from django.db import IntegrityError, connection, connections
from django.db.backends.sqlite3.base import DatabaseWrapper as SQLiteDatabaseWrapper
from django.db.migrations.exceptions import IrreversibleError
from django.db.migrations.executor import MigrationExecutor

from apps.catalog.models import Agency, Service, ServiceAgency, Unit, UnitService

cat_0002 = importlib.import_module("apps.catalog.migrations.0002_align_orm_state_with_schema")
sch_0002 = importlib.import_module("apps.search.migrations.0002_align_orm_state_with_schema")
gui_0002 = importlib.import_module("apps.guidance.migrations.0002_align_orm_state_with_schema")


def _make_isolated_sqlite_connection(db_path: str) -> SQLiteDatabaseWrapper:
    cfg = dict(settings.DATABASES["default"])
    cfg["ENGINE"] = "django.db.backends.sqlite3"
    cfg["NAME"] = db_path
    cfg["OPTIONS"] = {}
    conn = SQLiteDatabaseWrapper(cfg, alias="sqlite_mig_test")
    connections["sqlite_mig_test"] = conn
    conn.ensure_connection()
    return conn


@pytest.mark.django_db(transaction=True)
def test_sqlite_empty_initialization_and_populated_data_migration_preserves_all_records(tmp_path):
    """
    1. Testa inicialização de um SQLite vazio até as 14 migrations.
    2. Testa migração de um SQLite já populado em 0001_initial para 0002_align_orm_state_with_schema,
       comprovando preservação integral dos registros e relacionamentos nas 9 tabelas.
    """
    # Parte A: Inicialização de um SQLite completamente vazio aplicando todas as 14 migrations
    empty_db_path = str(tmp_path / "empty_init.sqlite3")
    conn_empty = _make_isolated_sqlite_connection(empty_db_path)
    try:
        executor_empty = MigrationExecutor(conn_empty)
        all_targets = executor_empty.loader.graph.leaf_nodes()
        executor_empty.migrate(all_targets)

        with conn_empty.cursor() as cur:
            cur.execute("SELECT count(*) FROM django_migrations;")
            assert cur.fetchone()[0] == 14
            cur.execute("PRAGMA foreign_key_check;")
            assert cur.fetchall() == []
    finally:
        conn_empty.close()

    # Parte B: Migração de um SQLite já populado em 0001_initial para 0002
    pop_db_path = str(tmp_path / "populated_0001.sqlite3")
    conn_pop = _make_isolated_sqlite_connection(pop_db_path)
    try:
        executor = MigrationExecutor(conn_pop)
        targets_0001 = [
            ("accounts", "0001_initial"),
            ("catalog", "0001_initial"),
            ("search", "0001_initial"),
            ("guidance", "0001_initial"),
        ]
        state_0001 = executor.migrate(targets_0001)
        apps_0001 = state_0001.apps

        # Cria registros usando os models históricos do estado 0001_initial
        Gender0001 = apps_0001.get_model("accounts", "Gender")
        InternalUser0001 = apps_0001.get_model("accounts", "InternalUser")
        Citizen0001 = apps_0001.get_model("accounts", "Citizen")
        Agency0001 = apps_0001.get_model("catalog", "Agency")
        Unit0001 = apps_0001.get_model("catalog", "Unit")
        Service0001 = apps_0001.get_model("catalog", "Service")
        NonWorkingDay0001 = apps_0001.get_model("catalog", "NonWorkingDay")
        ServiceAgency0001 = apps_0001.get_model("catalog", "ServiceAgency")
        UnitService0001 = apps_0001.get_model("catalog", "UnitService")
        Faq0001 = apps_0001.get_model("catalog", "Faq")
        ServiceVersion0001 = apps_0001.get_model("catalog", "ServiceVersion")
        QueryLog0001 = apps_0001.get_model("search", "QueryLog")
        Synonym0001 = apps_0001.get_model("search", "Synonym")
        GuidanceProgress0001 = apps_0001.get_model("guidance", "GuidanceProgress")
        GeneratedPdf0001 = apps_0001.get_model("guidance", "GeneratedPdf")

        gender = Gender0001.objects.using("sqlite_mig_test").create(
            name="Não Informado", sort_order=0, is_active=True
        )
        u_admin = InternalUser0001.objects.using("sqlite_mig_test").create(
            cpf="11122233344",
            full_name="Admin Mig",
            email="admin@sosp.gov.br",
            password_hash="hash",
            role="admin",
            can_manage_catalog=True,
        )
        cit = Citizen0001.objects.using("sqlite_mig_test").create(
            cpf="55566677788",
            full_name="Cidadao Mig",
            birth_date=datetime.date(1990, 1, 1),
            gender=gender,
            email="cid@sosp.gov.br",
            phone="82999990000",
            password_hash="hash",
            zip_code="57000000",
            street="Rua A",
            address_number="10",
            neighborhood="Centro",
            city="Maceio",
            state="AL",
        )
        ag1 = Agency0001.objects.using("sqlite_mig_test").create(
            name="Orgao 1", acronym="O1", sphere="state", is_active=True
        )
        ag2 = Agency0001.objects.using("sqlite_mig_test").create(
            name="Orgao 2", acronym="O2", sphere="state", is_active=True
        )
        un1 = Unit0001.objects.using("sqlite_mig_test").create(
            agency=ag1,
            name="Unidade 1",
            zip_code="57000000",
            street="Rua U",
            address_number="1",
            neighborhood="Centro",
            city="Maceio",
            state="AL",
            daily_limit=100,
        )
        srv1 = Service0001.objects.using("sqlite_mig_test").create(
            name="Servico 1",
            category="documents",
            detailed_description="Det 1",
            eligibility="Elig 1",
            is_free=True,
            average_deadline_days=5,
            channel="inPerson",
            status="active",
        )
        srv2 = Service0001.objects.using("sqlite_mig_test").create(
            name="Servico 2",
            category="taxes",
            detailed_description="Det 2",
            eligibility="Elig 2",
            is_free=True,
            average_deadline_days=3,
            channel="inPerson",
            status="active",
        )

        # 1. NonWorkingDay no estado 0001 (com is_recurring)
        nwd_nat = NonWorkingDay0001.objects.using("sqlite_mig_test").create(
            unit=None, day_date=datetime.date(2026, 12, 25), description="Natal", is_recurring=True
        )
        nwd_unit = NonWorkingDay0001.objects.using("sqlite_mig_test").create(
            unit=un1, day_date=datetime.date(2026, 12, 31), description="Recesso Unidade", is_recurring=False
        )

        # 2. ServiceAgency no estado 0001 (2 agências para o mesmo serviço srv1)
        ServiceAgency0001.objects.using("sqlite_mig_test").create(service=srv1, agency=ag1)
        ServiceAgency0001.objects.using("sqlite_mig_test").create(service=srv1, agency=ag2)

        # 3. UnitService no estado 0001 (2 serviços para a mesma unidade un1)
        UnitService0001.objects.using("sqlite_mig_test").create(unit=un1, service=srv1, is_active=True)
        UnitService0001.objects.using("sqlite_mig_test").create(unit=un1, service=srv2, is_active=False)

        # 4. Faq no estado 0001 (com sort_order)
        faq = Faq0001.objects.using("sqlite_mig_test").create(
            service=srv1,
            category="documents",
            question="Pergunta existente?",
            answer="Resposta preservada.",
            sort_order=10,
            is_active=True,
        )

        # 5. ServiceVersion no estado 0001 (com change_summary, approved_by, approved_at)
        sv = ServiceVersion0001.objects.using("sqlite_mig_test").create(
            service=srv1,
            version=1,
            snapshot={"name": "Servico 1"},
            change_summary="Versao inicial",
            created_by=u_admin.id,
        )

        # 6. QueryLog no estado 0001
        qlog = QueryLog0001.objects.using("sqlite_mig_test").create(
            term="identidade", filters={"category": "documents"}, result_count=4
        )

        # 7. Synonym no estado 0001
        syn = Synonym0001.objects.using("sqlite_mig_test").create(
            term="rg", synonyms=["carteira de identidade"], is_active=True
        )

        # 8. GuidanceProgress no estado 0001
        doc_uuid = uuid.uuid4()
        gp = GuidanceProgress0001.objects.using("sqlite_mig_test").create(
            citizen=cit, service=srv1, checked_document_ids=[doc_uuid]
        )

        # 9. GeneratedPdf no estado 0001
        pdf = GeneratedPdf0001.objects.using("sqlite_mig_test").create(
            citizen=cit,
            service=srv1,
            file_url="https://sosp.gov.br/pdfs/c1.pdf",
            expires_at=datetime.datetime(2026, 12, 31, 12, 0, tzinfo=datetime.timezone.utc),
        )

        # Agora executa as migrations 0002_align_orm_state_with_schema sobre o banco populado!
        executor_after = MigrationExecutor(conn_pop)
        state_after = executor_after.migrate(executor_after.loader.graph.leaf_nodes())
        apps_after = state_after.apps

        NonWorkingDayAfter = apps_after.get_model("catalog", "NonWorkingDay")
        ServiceAgencyAfter = apps_after.get_model("catalog", "ServiceAgency")
        UnitServiceAfter = apps_after.get_model("catalog", "UnitService")
        FaqAfter = apps_after.get_model("catalog", "Faq")
        ServiceVersionAfter = apps_after.get_model("catalog", "ServiceVersion")
        QueryLogAfter = apps_after.get_model("search", "QueryLog")
        SynonymAfter = apps_after.get_model("search", "Synonym")
        GuidanceProgressAfter = apps_after.get_model("guidance", "GuidanceProgress")
        GeneratedPdfAfter = apps_after.get_model("guidance", "GeneratedPdf")

        assert NonWorkingDayAfter.objects.using("sqlite_mig_test").get(id=nwd_nat.id).scope == "national"
        assert NonWorkingDayAfter.objects.using("sqlite_mig_test").get(id=nwd_unit.id).scope == "unit"

        sa_pairs = set(
            ServiceAgencyAfter.objects.using("sqlite_mig_test").values_list("service_id", "agency_id")
        )
        assert sa_pairs == {(srv1.id, ag1.id), (srv1.id, ag2.id)}

        us_triples = set(
            UnitServiceAfter.objects.using("sqlite_mig_test").values_list("unit_id", "service_id", "is_active")
        )
        assert us_triples == {(un1.id, srv1.id, True), (un1.id, srv2.id, False)}

        faq_after = FaqAfter.objects.using("sqlite_mig_test").get(id=faq.id)
        assert faq_after.question == "Pergunta existente?"
        assert faq_after.answer == "Resposta preservada."
        assert faq_after.service_id == srv1.id

        sv_after = ServiceVersionAfter.objects.using("sqlite_mig_test").get(id=sv.id)
        assert sv_after.service_id == srv1.id
        assert sv_after.version == 1
        assert sv_after.created_by_id == u_admin.id

        qlog_after = QueryLogAfter.objects.using("sqlite_mig_test").get(id=qlog.id)
        assert qlog_after.term == "identidade"
        assert qlog_after.result_count == 4
        assert qlog_after.session_hash is None

        syn_after = SynonymAfter.objects.using("sqlite_mig_test").get(id=syn.id)
        assert syn_after.term == "rg"
        assert syn_after.is_active is True

        gp_after = GuidanceProgressAfter.objects.using("sqlite_mig_test").get(id=gp.id)
        assert gp_after.citizen_id == cit.id
        assert gp_after.service_id == srv1.id
        assert gp_after.started_at is not None
        assert gp_after.completed_at is None

        pdf_after = GeneratedPdfAfter.objects.using("sqlite_mig_test").get(id=pdf.id)
        assert pdf_after.citizen_id == cit.id
        assert pdf_after.service_id == srv1.id
        assert pdf_after.file_url == "https://sosp.gov.br/pdfs/c1.pdf"
        assert pdf_after.checklist_hash == "legacy_migrated_hash"

        # Verifica PRAGMA foreign_key_check global, ausência de tabelas temporárias __new,
        # preservação das tabelas relacionadas (pais) e índices/constraints das tabelas reconstruídas
        with conn_pop.cursor() as cur:
            cur.execute("PRAGMA foreign_key_check;")
            assert cur.fetchall() == []

            cur.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name LIKE '%__new';")
            assert cur.fetchall() == []

            # Confirma que DROP TABLE nas tabelas-folha não afetou nenhuma tabela relacionada
            cur.execute("SELECT count(*) FROM catalogagency;")
            assert cur.fetchone()[0] == 2
            cur.execute("SELECT count(*) FROM catalogunit;")
            assert cur.fetchone()[0] == 1
            cur.execute("SELECT count(*) FROM catalogservice;")
            assert cur.fetchone()[0] == 2
            cur.execute("SELECT count(*) FROM accountsinternaluser;")
            assert cur.fetchone()[0] == 1
            cur.execute("SELECT count(*) FROM accountscitizen;")
            assert cur.fetchone()[0] == 1

            # Verifica índices reconstruídos nas tabelas alinhadas
            expected_indexes = {
                "catalognonworkingday": {"idx_nonworkingday_unitid", "idx_nonworkingday_daydate"},
                "catalogserviceagency": {"idx_serviceagency_agencyid"},
                "catalogunitservice": {"idx_unitservice_serviceid"},
                "catalogfaq": {"idx_faq_serviceid", "idx_faq_category"},
                "catalogserviceversion": {"idx_serviceversion_serviceid"},
                "searchquerylog": {"idx_searchquerylog_term", "idx_searchquerylog_createdat"},
                "guidanceprogress": {"idx_guidanceprogress_citizenid"},
                "guidancegeneratedpdf": {"idx_guidancepdf_citizenid", "idx_guidancepdf_expiresat"},
            }
            for tbl, req_idx in expected_indexes.items():
                cur.execute(f"PRAGMA index_list({tbl});")
                found_idx = {row[1] for row in cur.fetchall()}
                assert req_idx.issubset(found_idx), f"Índices ausentes em {tbl}: {req_idx - found_idx}"

            # Verifica PK composta física em catalogserviceagency e catalogunitservice
            cur.execute("PRAGMA table_info(catalogserviceagency);")
            sa_pk_cols = [row[1] for row in sorted(cur.fetchall(), key=lambda r: r[5]) if row[5] > 0]
            assert sa_pk_cols == ["serviceid", "agencyid"]

            cur.execute("PRAGMA table_info(catalogunitservice);")
            us_pk_cols = [row[1] for row in sorted(cur.fetchall(), key=lambda r: r[5]) if row[5] > 0]
            assert us_pk_cols == ["unitid", "serviceid"]
    finally:
        conn_pop.close()


@pytest.mark.django_db(transaction=True)
def test_sqlite_migration_fails_and_rolls_back_on_duplicate_or_conflicting_records(tmp_path):
    """
    Comprova que a migração SQLite:
    1. Não usa INSERT OR IGNORE (não descarta registros duplicados silenciosamente);
    2. Interrompe-se com IntegrityError explícito diante de duplicatas em catalogserviceagency,
       catalogunitservice ou catalogserviceversion, ou de FK órfã em catalogserviceversion;
    3. Faz rollback transacional completo, preservando o estado e os registros originais de 0001_initial.
    """
    scenarios = [
        "duplicate_serviceagency",
        "duplicate_unitservice",
        "duplicate_serviceversion",
        "orphan_fk_serviceversion",
        "duplicate_synonym_term",
    ]

    for scenario in scenarios:
        db_path = str(tmp_path / f"conflict_{scenario}.sqlite3")
        conn_conflict = _make_isolated_sqlite_connection(db_path)
        try:
            executor = MigrationExecutor(conn_conflict)
            targets_0001 = [
                ("accounts", "0001_initial"),
                ("catalog", "0001_initial"),
                ("search", "0001_initial"),
            ]
            state_0001 = executor.migrate(targets_0001)
            apps_0001 = state_0001.apps

            Agency0001 = apps_0001.get_model("catalog", "Agency")
            Unit0001 = apps_0001.get_model("catalog", "Unit")
            Service0001 = apps_0001.get_model("catalog", "Service")
            InternalUser0001 = apps_0001.get_model("accounts", "InternalUser")

            u_admin = InternalUser0001.objects.using("sqlite_mig_test").create(
                cpf="11122233344",
                full_name="Admin Conflict",
                email="admin@sosp.gov.br",
                password_hash="hash",
                role="admin",
                can_manage_catalog=True,
            )
            ag = Agency0001.objects.using("sqlite_mig_test").create(
                name="Orgao C", acronym="OC", sphere="state", is_active=True
            )
            un = Unit0001.objects.using("sqlite_mig_test").create(
                agency=ag,
                name="Unidade C",
                zip_code="57000000",
                street="Rua C",
                address_number="1",
                neighborhood="Centro",
                city="Maceio",
                state="AL",
                daily_limit=50,
            )
            srv = Service0001.objects.using("sqlite_mig_test").create(
                name="Servico C",
                category="documents",
                detailed_description="Det C",
                eligibility="Elig C",
                is_free=True,
                average_deadline_days=5,
                channel="inPerson",
                status="active",
            )

            with conn_conflict.cursor() as cur:
                if scenario == "duplicate_serviceagency":
                    # Simula base legada sem índice único contendo 2 linhas duplicadas (serviceid, agencyid)
                    cur.execute("PRAGMA index_list(catalogserviceagency);")
                    for idx_row in cur.fetchall():
                        if not idx_row[1].startswith("sqlite_autoindex"):
                            cur.execute(f'DROP INDEX IF EXISTS "{idx_row[1]}";')
                    cur.execute(
                        "INSERT INTO catalogserviceagency (serviceid, agencyid) VALUES (%s, %s), (%s, %s);",
                        [srv.id.hex, ag.id.hex, srv.id.hex, ag.id.hex],
                    )
                elif scenario == "duplicate_unitservice":
                    cur.execute("PRAGMA index_list(catalogunitservice);")
                    for idx_row in cur.fetchall():
                        if not idx_row[1].startswith("sqlite_autoindex"):
                            cur.execute(f'DROP INDEX IF EXISTS "{idx_row[1]}";')
                    cur.execute(
                        """
                        INSERT INTO catalogunitservice (unitid, serviceid, isactive, createdat)
                        VALUES (%s, %s, 1, '2026-01-01 00:00:00'), (%s, %s, 0, '2026-01-02 00:00:00');
                        """,
                        [un.id.hex, srv.id.hex, un.id.hex, srv.id.hex],
                    )
                elif scenario == "duplicate_serviceversion":
                    # No estado 0001_initial, catalogserviceversion não possuía unique(serviceid, version)
                    cur.execute(
                        """
                        INSERT INTO catalogserviceversion (id, serviceid, version, snapshot, createdby, createdat)
                        VALUES (%s, %s, 1, '{}', %s, '2026-01-01 00:00:00'),
                               (%s, %s, 1, '{}', %s, '2026-01-02 00:00:00');
                        """,
                        [
                            uuid.uuid4().hex,
                            srv.id.hex,
                            u_admin.id.hex,
                            uuid.uuid4().hex,
                            srv.id.hex,
                            u_admin.id.hex,
                        ],
                    )
                elif scenario == "orphan_fk_serviceversion":
                    # No estado 0001_initial, createdby era apenas UUIDField sem FK física
                    orphan_user_uuid = uuid.uuid4().hex
                    cur.execute(
                        """
                        INSERT INTO catalogserviceversion (id, serviceid, version, snapshot, createdby, createdat)
                        VALUES (%s, %s, 1, '{}', %s, '2026-01-01 00:00:00');
                        """,
                        [uuid.uuid4().hex, srv.id.hex, orphan_user_uuid],
                    )
                elif scenario == "duplicate_synonym_term":
                    # No estado 0001_initial, searchsynonym.term não possuía restrição UNIQUE
                    cur.execute(
                        """
                        INSERT INTO searchsynonym (id, term, synonyms, isactive, createdat, updatedat)
                        VALUES (%s, 'cnh', '["habilitacao"]', 1, '2026-01-01 00:00:00', '2026-01-01 00:00:00'),
                               (%s, 'cnh', '["carteira motorista"]', 1, '2026-01-02 00:00:00', '2026-01-02 00:00:00');
                        """,
                        [uuid.uuid4().hex, uuid.uuid4().hex],
                    )

            target_app = "search" if scenario == "duplicate_synonym_term" else "catalog"
            executor_fail = MigrationExecutor(conn_conflict)
            with pytest.raises(IntegrityError):
                executor_fail.migrate([(target_app, "0002_align_orm_state_with_schema")])

            # Verifica que o rollback transacional preservou o estado original 0001_initial
            with conn_conflict.cursor() as cur:
                cur.execute(
                    "SELECT count(*) FROM django_migrations WHERE app = %s AND name = '0002_align_orm_state_with_schema';",
                    [target_app],
                )
                assert cur.fetchone()[0] == 0

                cur.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name LIKE '%__new';")
                assert cur.fetchall() == []

                if target_app == "catalog":
                    # Confirma que a coluna legada isrecurring de catalognonworkingday ainda existe (rollback completo)
                    cur.execute("PRAGMA table_info(catalognonworkingday);")
                    cols_nwd = {r[1] for r in cur.fetchall()}
                    assert "isrecurring" in cols_nwd
                else:
                    # Confirma que searchquerylog não recebeu sessionhash e searchsynonym manteve updatedat e 2 linhas
                    cur.execute("PRAGMA table_info(searchquerylog);")
                    cols_qlog = {r[1] for r in cur.fetchall()}
                    assert "sessionhash" not in cols_qlog
                    cur.execute("PRAGMA table_info(searchsynonym);")
                    cols_syn = {r[1] for r in cur.fetchall()}
                    assert "updatedat" in cols_syn
                    cur.execute("SELECT count(*) FROM searchsynonym;")
                    assert cur.fetchone()[0] == 2

                # Confirma que nenhum registro original foi perdido no cenário de duplicata
                if scenario == "duplicate_serviceagency":
                    cur.execute("SELECT count(*) FROM catalogserviceagency;")
                    assert cur.fetchone()[0] == 2
                elif scenario == "duplicate_unitservice":
                    cur.execute("SELECT count(*) FROM catalogunitservice;")
                    assert cur.fetchone()[0] == 2
                elif scenario == "duplicate_serviceversion":
                    cur.execute("SELECT count(*) FROM catalogserviceversion;")
                    assert cur.fetchone()[0] == 2
        finally:
            conn_conflict.close()


@pytest.mark.django_db(transaction=True)
def test_0002_migrations_are_explicitly_irreversible(tmp_path):
    """
    Confirma que as migrations 0002_align_orm_state_with_schema (catalog, search, guidance)
    não possuem reverse_code falso (noop) e lançam IrreversibleError ao tentar reverter para 0001_initial.
    """
    db_path = str(tmp_path / "irreversible_test.sqlite3")
    conn_irrev = _make_isolated_sqlite_connection(db_path)
    try:
        executor = MigrationExecutor(conn_irrev)
        executor.migrate(executor.loader.graph.leaf_nodes())

        for app_label in ("catalog", "search", "guidance"):
            executor_rev = MigrationExecutor(conn_irrev)
            with pytest.raises(IrreversibleError):
                executor_rev.migrate([(app_label, "0001_initial")])
    finally:
        conn_irrev.close()


@pytest.mark.django_db
def test_composite_key_models_multiple_associations_and_safe_orm_operations():
    """
    Valida todas as operações e restrições de segurança em ServiceAgency e UnitService
    com múltiplas associações compartilhando a mesma primeira coluna.
    """
    a1 = Agency.objects.create(name="Agência Comp 1", acronym="AC1", sphere="state", is_active=True)
    a2 = Agency.objects.create(name="Agência Comp 2", acronym="AC2", sphere="state", is_active=True)
    u1 = Unit.objects.create(
        agency=a1,
        name="Unidade Comp 1",
        street="Rua 1",
        address_number="10",
        neighborhood="Centro",
        city="Maceió",
        state="AL",
        zip_code="57000000",
        daily_limit=50,
    )
    u2 = Unit.objects.create(
        agency=a2,
        name="Unidade Comp 2",
        street="Rua 2",
        address_number="20",
        neighborhood="Centro",
        city="Maceió",
        state="AL",
        zip_code="57000000",
        daily_limit=50,
    )
    s1 = Service.objects.create(
        name="Serviço Comp 1",
        detailed_description="D1",
        eligibility="E1",
        category="documents",
        channel="inPerson",
        is_free=True,
        average_deadline_days=5,
        status="active",
    )
    s2 = Service.objects.create(
        name="Serviço Comp 2",
        detailed_description="D2",
        eligibility="E2",
        category="taxes",
        channel="inPerson",
        is_free=True,
        average_deadline_days=3,
        status="active",
    )

    # 1. Criação de múltiplas associações compartilhando a primeira coluna
    sa_s1_a1 = ServiceAgency.objects.create(service=s1, agency=a1)
    sa_s1_a2 = ServiceAgency.objects.create(service=s1, agency=a2)
    sa_s2_a1 = ServiceAgency.objects.create(service=s2, agency=a1)

    us_u1_s1 = UnitService.objects.create(unit=u1, service=s1, is_active=True)
    us_u1_s2 = UnitService.objects.create(unit=u1, service=s2, is_active=True)
    us_u2_s1 = UnitService.objects.create(unit=u2, service=s1, is_active=True)

    assert ServiceAgency.objects.filter(service=s1).count() == 2
    assert UnitService.objects.filter(unit=u1).count() == 2

    # 2. Igualdade (__eq__) e hash (__hash__) baseados no par composto (composite_pk)
    assert sa_s1_a1 != sa_s1_a2
    assert len({sa_s1_a1, sa_s1_a2, sa_s2_a1}) == 3
    assert us_u1_s1 != us_u1_s2
    assert len({us_u1_s1, us_u1_s2, us_u2_s1}) == 3

    # 3. Leituras por tupla pk=(col1, col2) funcionam com precisão cirúrgica
    fetched_sa = ServiceAgency.objects.get(pk=(s1.id, a2.id))
    assert fetched_sa.service_id == s1.id and fetched_sa.agency_id == a2.id

    fetched_us = UnitService.objects.get(pk=(u1.id, s2.id))
    assert fetched_us.unit_id == u1.id and fetched_us.service_id == s2.id

    excluded_sa = list(ServiceAgency.objects.filter(service=s1).exclude(pk=(s1.id, a1.id)))
    assert len(excluded_sa) == 1 and excluded_sa[0].agency_id == a2.id

    # 4. Leituras/filtros por pk escalar ambíguo são explicitamente bloqueadas
    with pytest.raises(ValueError, match="pk"):
        ServiceAgency.objects.get(pk=s1.id)
    with pytest.raises(ValueError, match="pk"):
        ServiceAgency.objects.filter(pk=s1.id)
    with pytest.raises(ValueError, match="pk"):
        UnitService.objects.exclude(pk=u1.id)
    with pytest.raises(ValueError, match="pk"):
        UnitService.objects.filter(pk__in=[u1.id])

    # 5. Alteração de uma associação via save() e update_or_create() NÃO afeta as demais da mesma unidade
    us_u1_s1.is_active = False
    us_u1_s1.save()

    assert UnitService.objects.get(unit=u1, service=s1).is_active is False
    assert UnitService.objects.get(unit=u1, service=s2).is_active is True
    assert UnitService.objects.get(unit=u2, service=s1).is_active is True

    updated_us, created = UnitService.objects.update_or_create(
        unit=u1,
        service=s1,
        defaults={"is_active": True},
    )
    assert created is False
    assert updated_us.is_active is True
    assert UnitService.objects.get(unit=u1, service=s2).is_active is True

    # 6. Tentativa de mutar coluna da chave composta em instância existente é bloqueada
    loaded_sa = ServiceAgency.objects.get(service=s1, agency=a1)
    loaded_sa.agency = a2
    with pytest.raises(ValueError, match="chave primária composta"):
        loaded_sa.save()
    with pytest.raises(ValueError, match="chave composta"):
        loaded_sa.delete()

    # 7. update_or_create / get_or_create com chave parcial é bloqueado
    with pytest.raises(ValueError, match="ambas as colunas"):
        UnitService.objects.update_or_create(unit=u1, defaults={"is_active": False})
    with pytest.raises(ValueError, match="ambas as colunas"):
        ServiceAgency.objects.get_or_create(service=s1)

    # 8. Operações em lote baseadas em pk escalar (in_bulk, bulk_update) são bloqueadas
    with pytest.raises(ValueError, match="in_bulk"):
        UnitService.objects.in_bulk()
    with pytest.raises(ValueError, match="bulk_update"):
        UnitService.objects.bulk_update([us_u1_s1], ["is_active"])

    # 9. Exclusão de uma associação preserva rigorosamente os demais vínculos da mesma coluna líder
    sa_s1_a1_fresh = ServiceAgency.objects.get(service=s1, agency=a1)
    sa_s1_a1_fresh.delete()
    assert not ServiceAgency.objects.filter(service=s1, agency=a1).exists()
    assert ServiceAgency.objects.filter(service=s1, agency=a2).exists()
    assert ServiceAgency.objects.filter(service=s2, agency=a1).exists()

    UnitService.objects.filter(unit=u1, service=s1).delete()
    assert not UnitService.objects.filter(unit=u1, service=s1).exists()
    assert UnitService.objects.filter(unit=u1, service=s2).exists()
    assert UnitService.objects.filter(unit=u2, service=s1).exists()

    # 10. Violação de unicidade composta gera IntegrityError
    with pytest.raises(IntegrityError):
        ServiceAgency.objects.create(service=s1, agency=a2)

    # 11. _check_unique() só suprime W342 se _composite_key_fields e unique_together estiverem íntegros
    sa_field = ServiceAgency._meta.get_field("service")
    assert sa_field._check_unique() == []

    orig_composite = ServiceAgency._composite_key_fields
    try:
        ServiceAgency._composite_key_fields = ()
        warnings = sa_field._check_unique()
        assert any(w.id == "fields.W342" for w in warnings)
    finally:
        ServiceAgency._composite_key_fields = orig_composite


def test_postgresql_0002_migrations_are_strict_noop():
    """
    Confirma que as funções de banco das 3 migrations 0002 não executam
    nenhum comando SQL quando o vendor da conexão é 'postgresql'.
    """
    mock_schema_editor = MagicMock()
    mock_schema_editor.connection.vendor = "postgresql"

    cat_0002.align_sqlite_catalog_tables_forward(None, mock_schema_editor)
    sch_0002.align_sqlite_search_tables_forward(None, mock_schema_editor)
    gui_0002.align_sqlite_guidance_tables_forward(None, mock_schema_editor)

    mock_schema_editor.connection.cursor.assert_not_called()
