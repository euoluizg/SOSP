import pytest
from rest_framework.test import APIClient
from apps.accounts.services import validate_cpf, validate_birth_date, validate_password_strength
from apps.accounts.repositories import citizen_repository

client = APIClient()

def test_cpf_validation():
    # CPFs matematicamente válidos para testes
    assert validate_cpf("52998224725") is True
    assert validate_cpf("529.982.247-25") is True
    assert validate_cpf("00000000191") is True

    # CPFs inválidos
    assert validate_cpf("11111111111") is False
    assert validate_cpf("00000000000") is False
    assert validate_cpf("123456789") is False
    assert validate_cpf("52998224720") is False

def test_birth_date_validation():
    # Menor de 12 anos (RF-01)
    is_valid, msg = validate_birth_date("2020-01-01")
    assert is_valid is False
    assert "no mínimo 12 anos" in msg

    # Futuro
    is_valid, msg = validate_birth_date("2099-01-01")
    assert is_valid is False
    assert "não pode ser no futuro" in msg

    # Válido
    is_valid, _ = validate_birth_date("1995-05-10")
    assert is_valid is True

def test_password_strength():
    is_valid, errors = validate_password_strength("S0sp@2026!Fort3")
    assert is_valid is True
    assert len(errors) == 0

    is_valid, errors = validate_password_strength("12345")
    assert is_valid is False
    assert len(errors) > 0

def test_register_citizen_api():
    payload = {
        "fullName": "Novo Cidadão",
        "cpf": "52998224725",
        "birthDate": "1998-07-20",
        "motherName": "Mãe do Cidadão",
        "rg": "998877",
        "rgIssuer": "SSP/AL",
        "email": "novo.cidadao@exemplo.com.br",
        "phone": "82988776655",
        "password": "Senha@Forte2026!",
        "isPcd": False,
        "zipCode": "57000000",
        "street": "Rua Exemplo",
        "number": "42",
        "neighborhood": "Centro",
        "city": "Maceió",
        "state": "AL",
    }
    response = client.post("/api/v1/auth/register", payload, format="json")
    assert response.status_code == 201
    data = response.json()
    assert data["cpf"] == "52998224725"
    assert "passwordHash" not in data

def test_login_success_and_failure():
    # Sucesso
    resp_ok = client.post(
        "/api/v1/auth/login",
        {"cpf": "11144477705", "password": "S0sp@2026!Fort3"},
        format="json",
    )
    assert resp_ok.status_code == 200
    assert "token" in resp_ok.json()

    # Senha errada
    resp_fail = client.post(
        "/api/v1/auth/login",
        {"cpf": "11144477705", "password": "senha-incorreta"},
        format="json",
    )
    assert resp_fail.status_code == 401

def test_login_lockout_after_5_failures():
    test_cpf = "00000000191"
    # Registra tentativas falhas
    for _ in range(4):
        citizen_repository.record_failed_attempt(test_cpf)

    # 5ª falha ativa o bloqueio de 5 minutos (RN-29)
    resp = client.post(
        "/api/v1/auth/login",
        {"cpf": test_cpf, "password": "senha-errada"},
        format="json",
    )
    assert resp.status_code == 429
    assert "bloqueado por 5 minutos" in resp.json()["detail"].lower()
    citizen_repository.reset_failed_attempts(test_cpf)

