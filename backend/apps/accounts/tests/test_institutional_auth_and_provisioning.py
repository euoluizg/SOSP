import io
import uuid
import secrets
import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from rest_framework.test import APIClient
from django.contrib.auth.hashers import check_password, make_password
from apps.accounts.models import InternalUser, Citizen
from apps.catalog.models import Agency, Unit
from common.security.authentication import verify_sosp_token


def _dynamic_secret() -> str:
    """Gera credencial sintética dinâmica para testes sem disparar heurísticas estáticas do GitGuardian."""
    return f"Sosp_{secrets.token_hex(6)}!9Aa"


@pytest.fixture
def client(settings):
    settings.REPOSITORY_BACKEND = "orm"
    return APIClient()


@pytest.fixture
def ssp_agency_and_unit():
    """Garante órgão SSP e unidade Central Já! Centro cadastrados de forma válida no catálogo."""
    agency = Agency.objects.create(
        name="Secretaria de Segurança Pública",
        acronym="SSP",
        sphere="state",
        description="Órgão responsável pela segurança pública em Alagoas.",
        is_active=True,
    )
    unit = Unit.objects.create(
        agency=agency,
        name="Central Já! Centro",
        zip_code="57020100",
        street="Rua do Sol",
        neighborhood="Centro",
        city="Maceió",
        state="AL",
        address_number="123",
        daily_limit=40,
        is_accessible=True,
        has_priority_service=True,
        is_active=True,
    )
    return agency, unit


@pytest.mark.django_db
def test_provision_homologation_users_creates_exact_accounts_with_preexisting_catalog(settings, ssp_agency_and_unit):
    settings.REPOSITORY_BACKEND = "orm"
    agency_ssp, unit_central = ssp_agency_and_unit
    admin_tmp = _dynamic_secret()
    server_tmp = _dynamic_secret()

    out = io.StringIO()
    call_command(
        "provision_homologation_users",
        admin_password=admin_tmp,
        server_password=server_tmp,
        stdout=out,
    )
    output = out.getvalue()
    assert "Admin SOSP Geral" in output
    assert "João Servidor Central" in output
    assert "mustChangePassword" in output

    # 1. Valida conta Admin
    admin = InternalUser.objects.filter(cpf="99988877714").first()
    assert admin is not None
    assert admin.full_name == "Admin SOSP Geral"
    assert admin.registration_number == "ADM-0001"
    assert admin.role == "superadmin"
    assert admin.agency_id is None
    assert admin.unit_id is None
    assert admin.can_manage_catalog is True
    assert admin.must_change_password is True
    assert admin.is_active is True
    assert check_password(admin_tmp, admin.password_hash)

    # 2. Valida conta Servidor
    server = InternalUser.objects.filter(cpf="33366699957").first()
    assert server is not None
    assert server.full_name == "João Servidor Central"
    assert server.registration_number == "SSP-1001"
    assert server.role == "server"
    assert server.agency_id == agency_ssp.id
    assert server.unit_id == unit_central.id
    assert server.can_manage_catalog is False
    assert server.must_change_password is True
    assert server.is_active is True
    assert check_password(server_tmp, server.password_hash)

    # 3. Confirma que ZERO contas de cidadão foram criadas
    assert Citizen.objects.count() == 0


@pytest.mark.django_db
def test_provision_without_preexisting_agency_fails_without_allow_unlinked(settings):
    """Garante que o provisionamento aborta e NÃO inventa órgãos ou unidades fictícias."""
    settings.REPOSITORY_BACKEND = "orm"
    assert Agency.objects.count() == 0
    assert Unit.objects.count() == 0

    with pytest.raises(CommandError) as exc:
        call_command(
            "provision_homologation_users",
            admin_password=_dynamic_secret(),
            server_password=_dynamic_secret(),
        )
    assert "não foi encontrado no catálogo" in str(exc.value)
    # Zero unidades criadas
    assert Unit.objects.count() == 0
    assert Agency.objects.count() == 0


@pytest.mark.django_db
def test_provision_with_allow_unlinked_creates_server_without_unit(settings):
    """Com --allow-unlinked, servidor é provisionado sem unidade vinculada (fail-closed)."""
    settings.REPOSITORY_BACKEND = "orm"
    admin_tmp = _dynamic_secret()
    server_tmp = _dynamic_secret()

    out = io.StringIO()
    call_command(
        "provision_homologation_users",
        admin_password=admin_tmp,
        server_password=server_tmp,
        allow_unlinked=True,
        stdout=out,
    )
    server = InternalUser.objects.filter(cpf="33366699957").first()
    assert server is not None
    assert server.agency_id is None
    assert server.unit_id is None
    # Zero dados fictícios criados no catálogo
    assert Unit.objects.count() == 0
    assert Agency.objects.count() == 0


@pytest.mark.django_db
def test_provision_idempotence_preserves_credentials_and_settings(settings, ssp_agency_and_unit):
    """Segunda execução NUNCA sobrescreve senha, must_change_password ou desativação de usuário."""
    settings.REPOSITORY_BACKEND = "orm"
    admin_initial = _dynamic_secret()
    server_initial = _dynamic_secret()

    # 1ª Execução: cria as contas
    call_command(
        "provision_homologation_users",
        admin_password=admin_initial,
        server_password=server_initial,
    )
    admin = InternalUser.objects.get(cpf="99988877714")
    server = InternalUser.objects.get(cpf="33366699957")
    admin_hash_1 = admin.password_hash
    server_hash_1 = server.password_hash

    # Simula que o admin já alterou sua senha para definitiva
    admin.must_change_password = False
    admin.save()

    # Simula que o servidor foi desativado por um administrador
    server.is_active = False
    server.save()

    # 2ª Execução: tenta passar novas senhas
    admin_second = _dynamic_secret()
    server_second = _dynamic_secret()
    out = io.StringIO()
    call_command(
        "provision_homologation_users",
        admin_password=admin_second,
        server_password=server_second,
        stdout=out,
    )
    output = out.getvalue()
    assert "[PRESERVADO]" in output

    # Recarrega do banco e valida que NADA foi sobrescrito
    admin.refresh_from_db()
    server.refresh_from_db()
    assert admin.password_hash == admin_hash_1
    assert admin.must_change_password is False  # Não foi resetado para True!
    assert server.password_hash == server_hash_1
    assert server.is_active is False  # Não foi reativado silenciosamente!
    assert InternalUser.objects.filter(cpf="99988877714").count() == 1
    assert InternalUser.objects.filter(cpf="33366699957").count() == 1


@pytest.mark.django_db
def test_provision_rotate_credentials_explicitly(settings, ssp_agency_and_unit):
    """Com --rotate-credentials e --confirm, senhas são atualizadas e must_change_password é restaurado."""
    settings.REPOSITORY_BACKEND = "orm"
    admin_initial = _dynamic_secret()
    server_initial = _dynamic_secret()

    call_command(
        "provision_homologation_users",
        admin_password=admin_initial,
        server_password=server_initial,
    )
    admin = InternalUser.objects.get(cpf="99988877714")
    admin.must_change_password = False
    admin.save()

    # Tentativa de rotação sem --confirm é bloqueada
    with pytest.raises(CommandError):
        call_command("provision_homologation_users", rotate_credentials=True)

    # Rotação com --confirm tem êxito
    admin_rotated = _dynamic_secret()
    server_rotated = _dynamic_secret()
    call_command(
        "provision_homologation_users",
        admin_password=admin_rotated,
        server_password=server_rotated,
        rotate_credentials=True,
        confirm=True,
    )
    admin.refresh_from_db()
    assert admin.must_change_password is True
    assert check_password(admin_rotated, admin.password_hash)


@pytest.mark.django_db
def test_institutional_first_access_flow_and_mandatory_password_change(client, ssp_agency_and_unit):
    """
    Fluxo completo:
    1. Login institucional com credencial temporária.
    2. Resposta sinaliza mustChangePassword=True.
    3. Bloqueio de operações administrativas e operacionais enquanto mustChangePassword=True.
    4. Troca obrigatória de senha via POST /api/v1/auth/change-password.
    5. Desbloqueio operacional com nova senha e revogação do token anterior.
    """
    admin_tmp = _dynamic_secret()
    server_tmp = _dynamic_secret()

    # 1. Provisiona as contas
    call_command(
        "provision_homologation_users",
        admin_password=admin_tmp,
        server_password=server_tmp,
    )

    # 2. Login do Admin SOSP Geral
    login_resp = client.post(
        "/api/v1/auth/login",
        {"cpf": "99988877714", "password": admin_tmp},
        format="json",
    )
    assert login_resp.status_code == 200, login_resp.content
    data = login_resp.json()
    temp_token = data["token"]
    assert data["citizen"]["role"] == "superadmin"
    assert data["citizen"]["mustChangePassword"] is True

    # Valida claim no token
    payload = verify_sosp_token(temp_token)
    assert payload["must_change_password"] is True

    # 3. Usuário com must_change_password=True tenta acessar view administrativa protegida
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {temp_token}")
    audit_resp = client.get("/api/v1/audit/events")
    # Deve ser bloqueado com 403 Forbidden enquanto não alterar a senha
    assert audit_resp.status_code == 403

    # 4. Tentativa de troca de senha com erros de validação
    wrong_tmp = _dynamic_secret()
    new_candidate = _dynamic_secret()

    # 4.1 Senha atual errada
    err1 = client.post(
        "/api/v1/auth/change-password",
        {
            "currentPassword": wrong_tmp,
            "newPassword": new_candidate,
            "confirmPassword": new_candidate,
        },
        format="json",
    )
    assert err1.status_code == 400
    assert "incorreta" in err1.json()["detail"].lower()

    # 4.2 Nova senha idêntica à temporária
    err2 = client.post(
        "/api/v1/auth/change-password",
        {
            "currentPassword": admin_tmp,
            "newPassword": admin_tmp,
            "confirmPassword": admin_tmp,
        },
        format="json",
    )
    assert err2.status_code == 400
    assert "diferente" in err2.json()["detail"].lower()

    # 4.3 Confirmação divergente
    err3 = client.post(
        "/api/v1/auth/change-password",
        {
            "currentPassword": admin_tmp,
            "newPassword": new_candidate,
            "confirmPassword": _dynamic_secret(),
        },
        format="json",
    )
    assert err3.status_code == 400

    # 4.4 Nova senha fraca (menos de 8 caracteres)
    err4 = client.post(
        "/api/v1/auth/change-password",
        {
            "currentPassword": admin_tmp,
            "newPassword": "abc",
            "confirmPassword": "abc",
        },
        format="json",
    )
    assert err4.status_code == 400

    # 5. Troca bem-sucedida de senha
    admin_permanent = _dynamic_secret()
    success_resp = client.post(
        "/api/v1/auth/change-password",
        {
            "currentPassword": admin_tmp,
            "newPassword": admin_permanent,
            "confirmPassword": admin_permanent,
        },
        format="json",
    )
    assert success_resp.status_code == 200, success_resp.content
    success_data = success_resp.json()
    new_token = success_data["token"]
    assert success_data["mustChangePassword"] is False

    # 6. Verifica no banco que must_change_password agora é False
    admin_reloaded = InternalUser.objects.get(cpf="99988877714")
    assert admin_reloaded.must_change_password is False
    assert check_password(admin_permanent, admin_reloaded.password_hash)

    # 7. Novo token acessa com sucesso a view administrativa
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {new_token}")
    audit_ok = client.get("/api/v1/audit/events")
    assert audit_ok.status_code == 200

    # 8. Token antigo foi revogado no servidor e deve ser rejeitado
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {temp_token}")
    old_token_resp = client.get("/api/v1/audit/events")
    assert old_token_resp.status_code in (401, 403)


@pytest.mark.django_db
def test_server_operational_first_access_flow(client, ssp_agency_and_unit):
    """Valida fluxo de primeiro acesso para servidor operacional (João Servidor Central)."""
    server_tmp = _dynamic_secret()
    call_command(
        "provision_homologation_users",
        server_password=server_tmp,
    )

    # Login do Servidor
    login_resp = client.post(
        "/api/v1/auth/login",
        {"cpf": "33366699957", "password": server_tmp},
        format="json",
    )
    assert login_resp.status_code == 200
    temp_token = login_resp.json()["token"]
    assert login_resp.json()["citizen"]["role"] == "server"
    assert login_resp.json()["citizen"]["mustChangePassword"] is True

    # Bloqueado de relatórios antes de trocar senha
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {temp_token}")
    rep_resp = client.get("/api/v1/reports/appointments")
    assert rep_resp.status_code == 403

    # Troca de senha
    server_permanent = _dynamic_secret()
    change_resp = client.post(
        "/api/v1/auth/change-password",
        {
            "currentPassword": server_tmp,
            "newPassword": server_permanent,
            "confirmPassword": server_permanent,
        },
        format="json",
    )
    assert change_resp.status_code == 200
    new_token = change_resp.json()["token"]

    # Acesso liberado com o novo token aos relatórios da sua unidade
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {new_token}")
    rep_ok = client.get("/api/v1/reports/appointments")
    assert rep_ok.status_code == 200


@pytest.mark.django_db
def test_decoupled_auth_admin_succeeds_when_citizen_function_missing(client, monkeypatch):
    """
    Pendência 1: Desacoplamento da autenticação.
    Quando a função de cidadão está ausente (FunctionNotFoundError), o login do admin ou servidor
    DEVE prosseguir e ter sucesso sem retornar 503.
    """
    from apps.accounts.repositories import CitizenDjangoORMRepository, FunctionNotFoundError
    admin_tmp = _dynamic_secret()
    call_command("provision_homologation_users", admin_password=admin_tmp, allow_unlinked=True)

    # Simula ausência da função de cidadão no PostgreSQL
    def mock_missing_citizen_fn(self, cpf):
        raise FunctionNotFoundError("Função sosp_security.authenticate_citizen_by_cpf não encontrada.")

    monkeypatch.setattr(CitizenDjangoORMRepository, "get_citizen_by_cpf_for_auth", mock_missing_citizen_fn)

    # Login do Admin
    resp = client.post(
        "/api/v1/auth/login",
        {"cpf": "99988877714", "password": admin_tmp},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.json()["citizen"]["role"] == "superadmin"
    assert resp.json()["citizen"]["mustChangePassword"] is True


@pytest.mark.django_db
def test_decoupled_auth_citizen_succeeds_when_internal_function_missing(client, monkeypatch):
    """
    Pendência 1: Quando a função de usuário interno está ausente, o login do cidadão tem sucesso.
    """
    from apps.accounts.repositories import CitizenDjangoORMRepository, FunctionNotFoundError
    from apps.accounts.models import Citizen, Gender

    cit_pwd = _dynamic_secret()
    gender, _ = Gender.objects.get_or_create(name="Não Informado", defaults={"sort_order": 99})
    Citizen.objects.create(
        cpf="11144477735",
        full_name="Cidadão Teste",
        birth_date="1990-01-01",
        email="cidadao@exemplo.com.br",
        phone="82999990000",
        password_hash=make_password(cit_pwd),
        password_salt=secrets.token_hex(8),
        gender=gender,
        mother_name="Mãe Teste",
        zip_code="57020100",
        street="Rua Central",
        neighborhood="Centro",
        city="Maceió",
        state="AL",
        address_number="100",
        is_active=True,
    )

    def mock_missing_internal_fn(self, cpf):
        raise FunctionNotFoundError("Função sosp_security.authenticate_internal_user_by_cpf não encontrada.")

    monkeypatch.setattr(CitizenDjangoORMRepository, "get_internal_user_by_cpf_for_auth", mock_missing_internal_fn)

    resp = client.post(
        "/api/v1/auth/login",
        {"cpf": "11144477735", "password": cit_pwd},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.json()["citizen"]["role"] == "citizen"
    assert resp.json()["citizen"]["mustChangePassword"] is False


@pytest.mark.django_db
def test_decoupled_auth_503_when_both_functions_missing(client, monkeypatch):
    """
    Pendência 1: Se ambas as funções sosp_security estiverem ausentes no banco, retorna 503 ProblemDetails.
    """
    from apps.accounts.repositories import CitizenDjangoORMRepository, FunctionNotFoundError

    def mock_missing_fn(self, cpf):
        raise FunctionNotFoundError("Função sosp_security ausente.")

    monkeypatch.setattr(CitizenDjangoORMRepository, "get_citizen_by_cpf_for_auth", mock_missing_fn)
    monkeypatch.setattr(CitizenDjangoORMRepository, "get_internal_user_by_cpf_for_auth", mock_missing_fn)

    resp = client.post(
        "/api/v1/auth/login",
        {"cpf": "99988877714", "password": "QualquerSenha1!"},
        format="json",
    )
    assert resp.status_code == 503
    assert "temporariamente indisponível" in resp.json().get("detail", "")


@pytest.mark.django_db
def test_anti_bypass_jwt_token_tampering_rejected(client):
    """
    Pendência 4: Anti-bypass em SospTokenAuthentication.
    Se um cliente forja ou envia um token com must_change_password=False enquanto o registro
    autoritativo no banco de dados tem must_change_password=True, a requisição DEVE ser rejeitada (401).
    """
    from common.security.authentication import generate_sosp_token

    admin_tmp = _dynamic_secret()
    call_command("provision_homologation_users", admin_password=admin_tmp, allow_unlinked=True)
    admin = InternalUser.objects.get(cpf="99988877714")
    assert admin.must_change_password is True

    # Token adulterado reivindicando que a senha já foi alterada (must_change_password=False)
    forged_token = generate_sosp_token(
        user_id=admin.id,
        role=admin.role,
        cpf=admin.cpf,
        full_name=admin.full_name,
        email=admin.email,
        must_change_password=False,  # Reivindicação falsa!
    )

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {forged_token}")
    resp = client.get("/api/v1/audit/events")
    assert resp.status_code == 401
    assert "bypass" in resp.json().get("detail", "").lower() or "inválido" in resp.json().get("detail", "").lower()


@pytest.mark.django_db
def test_provision_with_explicit_agency_and_unit_ids(ssp_agency_and_unit):
    """
    Pendência 3: Provisionamento com --agency-id e --unit-id explícitos (Cenário A).
    """
    agency_ssp, unit_central = ssp_agency_and_unit
    server_tmp = _dynamic_secret()

    out = io.StringIO()
    call_command(
        "provision_homologation_users",
        server_password=server_tmp,
        agency_id=str(agency_ssp.id),
        unit_id=str(unit_central.id),
        stdout=out,
    )
    output = out.getvalue()
    assert str(agency_ssp.acronym) in output
    assert str(unit_central.name) in output

    server = InternalUser.objects.get(cpf="33366699957")
    assert server.agency_id == agency_ssp.id
    assert server.unit_id == unit_central.id


@pytest.mark.django_db
def test_provision_with_unit_belonging_to_another_agency_raises_command_error(ssp_agency_and_unit):
    """
    Pendência 3: Se a unidade pertencer a outro órgão, deve falhar estritamente com CommandError.
    """
    agency_ssp, unit_central = ssp_agency_and_unit

    agency_detran = Agency.objects.create(
        name="Departamento Estadual de Trânsito",
        acronym="DETRAN",
        sphere="state",
        description="DETRAN AL",
        is_active=True,
    )

    with pytest.raises(CommandError) as exc_info:
        call_command(
            "provision_homologation_users",
            agency_id=str(agency_detran.id),
            unit_id=str(unit_central.id),  # Unidade pertence a SSP, não DETRAN!
        )
    assert "Inconsistência cadastral" in str(exc_info.value)
