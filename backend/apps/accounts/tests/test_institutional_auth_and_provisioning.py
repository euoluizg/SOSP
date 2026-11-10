import io
import uuid
import secrets
import pytest
from django.core.management import call_command
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


@pytest.mark.django_db
def test_provision_homologation_users_creates_exact_accounts(settings):
    settings.REPOSITORY_BACKEND = "orm"
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
    assert server.agency_id is not None
    assert server.unit_id is not None
    assert server.can_manage_catalog is False
    assert server.must_change_password is True
    assert server.is_active is True
    assert check_password(server_tmp, server.password_hash)

    # 3. Confirma que a lotação vinculada existe
    agency = Agency.objects.get(id=server.agency_id)
    assert agency.acronym == "SSP"
    unit = Unit.objects.get(id=server.unit_id)
    assert "Central" in unit.name

    # 4. Confirma que ZERO contas de cidadão foram criadas
    assert Citizen.objects.count() == 0

    # 5. Idempotência: rodar novamente não cria duplicatas nem falha
    call_command(
        "provision_homologation_users",
        admin_password=admin_tmp,
        server_password=server_tmp,
        stdout=out,
    )
    assert InternalUser.objects.filter(cpf="99988877714").count() == 1
    assert InternalUser.objects.filter(cpf="33366699957").count() == 1


@pytest.mark.django_db
def test_institutional_first_access_flow_and_mandatory_password_change(client):
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
def test_server_operational_first_access_flow(client):
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
