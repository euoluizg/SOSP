import pytest
from rest_framework.test import APIClient

client = APIClient()

def test_rfc7807_error_contract():
    # Rota que não existe
    response = client.get("/api/v1/rota-inexistente-404")
    assert response.status_code == 404
    assert response["Content-Type"] == "application/problem+json"
    data = response.json()
    assert "type" in data
    assert "title" in data
    assert "status" in data
    assert "detail" in data
    assert "instance" in data
    assert "traceId" in data

def test_feature_flag_reviews_disabled():
    # Avaliação desativada no MVP (ADR-007)
    response = client.post("/api/v1/feedback/reviews/20261105-1042", {"rating": 5}, format="json")
    assert response.status_code == 403
    assert "desativado" in response.json()["detail"].lower()

def test_faq_endpoint():
    response = client.get("/api/v1/feedback/faq")
    assert response.status_code == 200
    faqs = response.json()
    assert len(faqs) >= 2
    assert any("Gov.br" in f["question"] for f in faqs)

def test_open_question_endpoint():
    payload = {
        "citizenName": "Maria Silva",
        "email": "maria@exemplo.com",
        "category": "Documentos",
        "subject": "Dúvida sobre certidão",
        "description": "Precisa ser certidão atualizada com menos de 90 dias?",
    }
    response = client.post("/api/v1/questions/", payload, format="json")
    assert response.status_code == 201
    assert "protocolNumber" in response.json()

@pytest.mark.django_db
def test_health_check_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert "database" in data
    assert data["database"]["status"] == "operational"

