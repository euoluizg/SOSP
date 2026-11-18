import secrets

import pytest

from apps.accounts.models import Citizen, Gender


pytestmark = pytest.mark.django_db


@pytest.fixture
def registration(settings):
    settings.REPOSITORY_BACKEND = "orm"
    return {
        "fullName": "Pessoa de Teste",
        "cpf": "00000000191",
        "birthDate": "1995-04-10",
        "motherName": "Pessoa Teste Mãe",
        "email": "cadastro@example.test",
        "phone": "82991122334",
        "password": f"Test_{secrets.token_urlsafe(12)}!1",
        "zipCode": "57020100",
        "street": "Rua de Teste",
        "number": "50",
        "neighborhood": "Centro",
        "city": "Maceió",
        "state": "AL",
    }


@pytest.mark.parametrize(
    ("gender", "expected"),
    [
        ("F", "Feminino"),
        ("M", "Masculino"),
        ("O", "Outro"),
        ("N", "Prefiro não informar"),
        ("", "Prefiro não informar"),
    ],
)
def test_register_uses_seeded_reference(api_client, registration, gender, expected):
    registration["gender"] = gender
    if gender == "O":
        registration["genderDescription"] = "Descrição de teste"

    response = api_client.post("/api/v1/auth/register", registration, format="json")

    assert response.status_code == 201
    citizen = Citizen.objects.get(cpf=registration["cpf"])
    assert citizen.gender.name == expected
    assert citizen.gender_description == registration.get("genderDescription", "")


def test_register_without_canonical_opt_out_accepts_legacy_reference(api_client, registration):
    Gender.objects.filter(name="Prefiro não informar").update(is_active=False)
    legacy = Gender.objects.create(name="Não Informado", sort_order=99)

    response = api_client.post("/api/v1/auth/register", registration, format="json")

    assert response.status_code == 201
    assert Citizen.objects.get(cpf=registration["cpf"]).gender_id == legacy.id


def test_register_without_active_reference_returns_problem_details(api_client, registration):
    Gender.objects.filter(name="Outro").update(is_active=False)
    reference_count = Gender.objects.count()
    registration["gender"] = "O"

    response = api_client.post("/api/v1/auth/register", registration, format="json")

    assert response.status_code == 503
    assert response["Content-Type"] == "application/problem+json"
    assert response.json()["status"] == 503
    assert not Citizen.objects.filter(cpf=registration["cpf"]).exists()
    assert Gender.objects.count() == reference_count


def test_register_rejects_unknown_gender_code(api_client, registration):
    registration["gender"] = "?"

    response = api_client.post("/api/v1/auth/register", registration, format="json")

    assert response.status_code == 400
    assert response.json()["errors"][0]["field"] == "gender"
    assert not Citizen.objects.filter(cpf=registration["cpf"]).exists()
