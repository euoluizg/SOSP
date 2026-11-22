import pytest
from rest_framework.test import APIClient

client = APIClient()

def test_list_agencies():
    response = client.get("/api/v1/agencies/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3
    assert any(a["acronym"] == "SSP" for a in data)

def test_list_units():
    response = client.get("/api/v1/units/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3
    assert any("Central Já!" in u["name"] for u in data)

def test_get_service_detail_success():
    response = client.get("/api/v1/services/servico-emitir-rg")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Emitir Carteira de Identidade Nacional (CIN)"
    assert "steps" in data
    assert "documents" in data
    assert "estimatedDuration" in data
    assert "cost" in data

def test_get_service_detail_not_found():
    response = client.get("/api/v1/services/servico-inexistente")
    assert response.status_code == 404
    assert response["Content-Type"] == "application/problem+json"
    assert response.json()["status"] == 404

def test_list_categories():
    response = client.get("/api/v1/categories/")
    assert response.status_code == 200
    categories = response.json()
    assert "Documentos Pessoais" in categories

