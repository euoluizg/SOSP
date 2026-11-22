import pytest
from rest_framework.test import APIClient

client = APIClient()

def test_search_services_pagination():
    response = client.get("/api/v1/services/?page=1&pageSize=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "totalPages" in data
    assert data["pageSize"] == 10
    assert len(data["items"]) <= 10

def test_search_services_by_query():
    response = client.get("/api/v1/services/?query=identidade")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any("Identidade" in s["name"] for s in data["items"])

def test_search_services_by_category():
    response = client.get("/api/v1/services/?category=Documentos%20Pessoais")
    assert response.status_code == 200
    data = response.json()
    assert all(s["category"] == "Documentos Pessoais" for s in data["items"])

def test_search_services_by_channel():
    response = client.get("/api/v1/services/?channel=inPerson")
    assert response.status_code == 200
    data = response.json()
    assert all(s["channel"] == "inPerson" for s in data["items"])

