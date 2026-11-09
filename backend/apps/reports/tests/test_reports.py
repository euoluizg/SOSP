import pytest

# Relatórios exigem autenticação (REST_FRAMEWORK.DEFAULT_PERMISSION_CLASSES).
# O fixture `auth_client` (backend/conftest.py) autentica via /auth/login.

def test_reports_appointments_summary(auth_client):
    response = auth_client.get("/api/v1/reports/appointments")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "totalAppointments" in data["metrics"]
    assert "scheduled" in data["metrics"]
    assert "completed" in data["metrics"]
    assert "recentQueue" in data

def test_reports_export_csv(auth_client):
    payload = {"type": "csv", "filters": {"agencyId": "orgao-ssp"}}
    response = auth_client.post("/api/v1/reports/exports", payload, format="json")
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "csv"
    assert data["status"] == "ready"
    assert "downloadUrl" in data
