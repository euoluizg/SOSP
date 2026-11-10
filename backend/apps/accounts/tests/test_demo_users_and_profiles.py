import pytest
import secrets
from rest_framework.test import APIClient
from apps.accounts.repositories import get_demo_password, CitizenDjangoORMRepository, CitizenInMemoryRepository
from apps.accounts.services import AccountService
from apps.accounts.models import InternalUser, Citizen, Gender
from django.contrib.auth.hashers import make_password

@pytest.fixture
def api_client():
    return APIClient()


def test_citizen_demo_login(api_client):
    """Cidadão 1 e Cidadão 2 autenticam com sucesso e recebem perfil citizen."""
    pwd = get_demo_password()
    # Cidadão 1
    resp1 = api_client.post("/api/v1/auth/login", {"cpf": "11144477735", "password": pwd})
    assert resp1.status_code == 200
    d1 = resp1.json()
    assert d1["citizen"]["role"] == "citizen"
    assert "token" in d1

    # Cidadão 2 (Maria Silva)
    resp2 = api_client.post("/api/v1/auth/login", {"cpf": "22255588846", "password": pwd})
    assert resp2.status_code == 200
    d2 = resp2.json()
    assert d2["citizen"]["role"] == "citizen"
    assert d2["citizen"]["fullName"] == "Maria Santos Silva"


def test_server_demo_login(api_client):
    """Servidor Central SSP autentica e recebe papel server com lotação correta."""
    pwd = get_demo_password()
    resp = api_client.post("/api/v1/auth/login", {"cpf": "33366699957", "password": pwd})
    assert resp.status_code == 200
    d = resp.json()
    assert d["citizen"]["role"] == "server"
    assert d["citizen"]["agencyId"] == "orgao-ssp"
    assert d["citizen"]["unitId"] == "unidade-centro"


def test_manager_demo_login(api_client):
    """Gestor institucional SSP autentica e recebe papel gestor com agência vinculada."""
    pwd = get_demo_password()
    resp = api_client.post("/api/v1/auth/login", {"cpf": "55588811194", "password": pwd})
    assert resp.status_code == 200
    d = resp.json()
    assert d["citizen"]["role"] == "gestor"
    assert d["citizen"]["agencyId"] == "orgao-ssp"


def test_admin_demo_login(api_client):
    """Superadministrador SOSP autentica e recebe papel superadmin."""
    pwd = get_demo_password()
    resp = api_client.post("/api/v1/auth/login", {"cpf": "99988877714", "password": pwd})
    assert resp.status_code == 200
    d = resp.json()
    assert d["citizen"]["role"] == "superadmin"


def test_legacy_cpf_alias_support(api_client):
    """Garante compatibilidade retroativa para testes com CPF anterior 11144477705."""
    pwd = get_demo_password()
    resp = api_client.post("/api/v1/auth/login", {"cpf": "11144477705", "password": pwd})
    assert resp.status_code == 200
    d = resp.json()
    assert d["citizen"]["id"] == "citizen-001"


def test_register_citizen_with_gender_description(api_client):
    """Cadastro aceita e valida genderDescription quando opção 'Outro' for selecionada."""
    test_pwd = f"Pass_{secrets.token_urlsafe(8)}!1"
    payload = {
        "fullName": "Pessoa Autodeclarada",
        "cpf": "10012345610",
        "birthDate": "1995-04-10",
        "gender": "O",
        "genderDescription": "Não-Binário Transmasculino",
        "motherName": "Maria Aparecida Silva",
        "email": "autodeclarado@exemplo.com.br",
        "phone": "82991122334",
        "mobilePhone": "82991122334",
        "password": test_pwd,
        "isPcd": False,
        "cep": "57020100",
        "zipCode": "57020100",
        "street": "Rua do Comércio",
        "number": "50",
        "neighborhood": "Centro",
        "city": "Maceió",
        "state": "AL",
    }
    resp = api_client.post("/api/v1/auth/register", payload, format="json")
    assert resp.status_code == 201
    data = resp.json()
    assert data["cpf"] == "10012345610"
    assert "passwordHash" not in data


def test_password_recovery_generates_dynamic_code(api_client):
    """Recuperação de senha gera código criptograficamente seguro e valida redefinição."""
    original_pwd = get_demo_password()
    try:
        # Solicita recuperação para o Cidadão 1
        resp = api_client.post("/api/v1/auth/recover-password", {"cpf": "11144477735"}, format="json")
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
        # Em ambiente de teste/debug, codeSimulated é retornado dinamicamente
        assert "codeSimulated" in data
        code = data["codeSimulated"]
        assert len(code) == 6
        assert code.isdigit()

        # Redefine a senha com o código dinâmico gerado
        new_pwd = f"NewPass_{secrets.token_urlsafe(8)}!1"
        reset_resp = api_client.post("/api/v1/auth/reset-password", {
            "cpf": "11144477735",
            "code": code,
            "newPassword": new_pwd,
        }, format="json")
        assert reset_resp.status_code == 200

        # Valida login com a nova senha
        login_resp = api_client.post("/api/v1/auth/login", {
            "cpf": "11144477735",
            "password": new_pwd,
        }, format="json")
        assert login_resp.status_code == 200
    finally:
        # Restaura a credencial original de citizen-001 para não vazar estado nos fixtures de outros testes
        from apps.accounts.repositories import citizen_repository
        from django.contrib.auth.hashers import make_password
        c = citizen_repository.get_by_id("citizen-001")
        if c:
            c["passwordHash"] = make_password(original_pwd)
        citizen_repository.reset_failed_attempts("11144477735")
        citizen_repository.reset_failed_attempts("11144477705")


@pytest.mark.django_db
def test_orm_repository_authenticates_internal_user():
    """Valida que o repositório ORM autentica InternalUser e resolve papéis institucionais."""
    pwd = f"InternalPass_{secrets.token_urlsafe(8)}!1"
    pwd_hash = make_password(pwd)
    u = InternalUser.objects.create(
        cpf="88877766655",
        full_name="Fiscal da Receita",
        email="fiscal@sefaz.al.gov.br",
        role="gestor",
        registration_number="SEF-8899",
        password_hash=pwd_hash,
        is_active=True,
    )

    repo = CitizenDjangoORMRepository()
    auth_data = repo.get_by_cpf_for_auth("88877766655")
    assert auth_data is not None
    assert auth_data["fullName"] == "Fiscal da Receita"
    assert auth_data["role"] == "gestor"
    assert auth_data["id"] == str(u.id)


@pytest.mark.django_db
def test_seed_demo_users_command_execution(capsys):
    """Garante que seed_demo_users executa sem erros, popula lotações e protege credenciais em stdout."""
    from django.core.management import call_command
    from apps.catalog.models import Agency

    call_command("seed_demo_users")
    captured = capsys.readouterr()
    out = captured.out

    # 1. Verifica ausência de vazamento de credenciais em logs compartilhados / stdout
    assert "Credencial:" not in out
    assert "A1!" not in out
    assert "[SEGURANÇA] Credencial temporária gerada e aplicada com sucesso" in out

    # 2. Verifica nomes corretos dos usuários internos e ausência de erro de campo name vs full_name
    assert "João Servidor Central" in out
    assert "Ana Servidora Farol" in out
    assert "Carlos Gestor SSP" in out
    assert "Admin SOSP Geral" in out

    # 3. Valida persistência e lotação institucional no banco
    ssp = Agency.objects.filter(acronym="SSP").first()
    assert ssp is not None

    servant = InternalUser.objects.filter(cpf="33366699957").first()
    assert servant is not None
    assert servant.full_name == "João Servidor Central"
    assert servant.agency_id == ssp.id
    assert servant.can_manage_catalog is False
    assert servant.role == "servant"

    gestor = InternalUser.objects.filter(cpf="55588811194").first()
    assert gestor is not None
    assert gestor.full_name == "Carlos Gestor SSP"
    assert gestor.agency_id == ssp.id
    assert gestor.can_manage_catalog is True
    assert gestor.role == "gestor"


@pytest.mark.django_db
def test_password_reset_orm_persists_to_db_and_invalidates_code():
    """Valida persistência de nova senha no ORM, invalidação contra replay e revogação de sessões."""
    from apps.accounts.models import Citizen, Session, Gender
    from django.utils import timezone
    import datetime

    g, _ = Gender.objects.get_or_create(name="Masculino", defaults={"sort_order": 1})
    cpf = "12309845678"
    old_pwd = "OldPassword!1"
    citizen = Citizen.objects.create(
        cpf=cpf,
        full_name="Cidadão Teste ORM",
        email="cidadao.orm@exemplo.com.br",
        phone="82999998888",
        gender=g,
        birth_date="1992-03-01",
        mother_name="Mãe Teste",
        street="Rua A",
        address_number="10",
        neighborhood="Centro",
        city="Maceió",
        state="AL",
        zip_code="57020000",
        password_hash=make_password(old_pwd),
        is_active=True,
    )

    token_hash = "token_hash_abc_123"
    sess = Session.objects.create(
        subject_type="citizen",
        subject_id=citizen.id,
        token_hash=token_hash,
        expires_at=timezone.now() + datetime.timedelta(minutes=30),
    )

    repo = CitizenDjangoORMRepository()

    # 1. Solicita e grava código de recuperação
    recovery_code = "789012"
    repo.set_recovery_code(cpf, recovery_code)
    assert repo.verify_recovery_code(cpf, recovery_code) is True
    assert repo.verify_recovery_code(cpf, "000000") is False

    # 2. Atualiza senha no ORM com o código validado
    new_pwd = "NewSecurePassword!2"
    new_hash = make_password(new_pwd)
    updated = repo.update_password(cpf, new_hash, code=recovery_code)
    assert updated is True

    # 3. Invalida código de recuperação e revoga sessões ativas
    repo.clear_recovery_code(cpf)
    assert repo.verify_recovery_code(cpf, recovery_code) is False

    repo.revoke_all_sessions(str(citizen.id))

    # 4. Verifica persistência real no banco de dados
    citizen.refresh_from_db()
    assert citizen.password_hash == new_hash
    assert citizen.recovery_code_hash is None

    sess.refresh_from_db()
    assert sess.revoked_at is not None
    assert repo.is_session_revoked(token_hash) is True


@pytest.mark.django_db
def test_password_reset_internal_user_orm_invalidation():
    """Valida recuperação e invalidação de código para usuários internos no ORM."""
    cpf = "98765432109"
    u = InternalUser.objects.create(
        cpf=cpf,
        full_name="Servidor Recuperacao",
        email="servidor.recuperacao@ssp.al.gov.br",
        role="servant",
        registration_number="SSP-9999",
        password_hash=make_password("OldServantPass!1"),
        is_active=True,
    )

    repo = CitizenDjangoORMRepository()
    code = "456789"
    repo.set_recovery_code(cpf, code)
    assert repo.verify_recovery_code(cpf, code) is True

    new_hash = make_password("NewServantPass!2")
    assert repo.update_password(cpf, new_hash) is True

    repo.clear_recovery_code(cpf)
    assert repo.verify_recovery_code(cpf, code) is False

    u.refresh_from_db()
    assert u.password_hash == new_hash


@pytest.mark.django_db
def test_gender_description_persistence_in_orm_repository():
    """Valida que genderDescription é persistido pelo repositório ORM e retornado na leitura."""
    from apps.accounts.models import Gender

    Gender.objects.get_or_create(name="Outro", defaults={"sort_order": 3})
    repo = CitizenDjangoORMRepository()

    cpf = "32165498701"
    data = {
        "cpf": cpf,
        "fullName": "Pessoa de Gênero Fluido",
        "email": "fluido@exemplo.com.br",
        "birthDate": "1994-06-18",
        "gender": "O",
        "genderDescription": "Não-Binário Fluido",
        "motherName": "Mãe Acolhedora",
        "phone": "82987654321",
        "zipCode": "57030000",
        "street": "Rua das Flores",
        "number": "12",
        "neighborhood": "Farol",
        "city": "Maceió",
        "state": "AL",
        "passwordHash": make_password("PwdTest!123"),
    }

    saved = repo.save(data)
    assert saved["genderDescription"] == "Não-Binário Fluido"

    # Confere no banco real
    c = Citizen.objects.get(cpf=cpf)
    assert c.gender_description == "Não-Binário Fluido"

    # Confere via leitura no repositório
    retrieved = repo.get_by_id(str(c.id))
    assert retrieved is not None
    assert retrieved["genderDescription"] == "Não-Binário Fluido"


def test_postgresql_internal_user_auth_mapping(monkeypatch):
    """Simula retorno da função sosp_security.authenticate_internal_user_by_cpf e valida mapeamento."""
    import uuid
    from django.db import connection

    fake_user_id = uuid.uuid4()
    fake_agency_id = uuid.uuid4()
    fake_unit_id = uuid.uuid4()
    clean_cpf = "33366699957"

    class FakeCursor:
        def __init__(self):
            self.call_count = 0

        def execute(self, sql, params):
            self.last_sql = sql
            self.call_count += 1

        def fetchone(self):
            # Na 1ª chamada (authenticate_citizen_by_cpf), retorna None
            if self.call_count == 1:
                return None
            # Na 2ª chamada (authenticate_internal_user_by_cpf), retorna dados do servidor operacional com unitId
            return (
                fake_user_id,
                "João Servidor Central",
                "joao.servidor@ssp.al.gov.br",
                "SSP-1001",
                fake_agency_id,
                fake_unit_id,
                "servant",
                False,
                "argon2_hash_dummy",
                True,
            )

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    monkeypatch.setattr(connection, "vendor", "postgresql")
    monkeypatch.setattr(connection, "cursor", lambda: FakeCursor())

    repo = CitizenDjangoORMRepository()
    auth_data = repo.get_by_cpf_for_auth(clean_cpf)

    assert auth_data is not None
    assert auth_data["id"] == str(fake_user_id)
    assert auth_data["fullName"] == "João Servidor Central"
    assert auth_data["role"] == "server"
    assert auth_data["agencyId"] == str(fake_agency_id)
    assert auth_data["unitId"] == str(fake_unit_id)
    assert auth_data["canManageCatalog"] is False
    assert auth_data["isActive"] is True

