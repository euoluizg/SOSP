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
