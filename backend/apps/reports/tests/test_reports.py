import pytest
from rest_framework.test import APIClient

client = APIClient()

def test_reports_appointments_summary():
    response = client.get("/api/v1/reports/appointments")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "totalAppointments" in data["metrics"]
    assert "scheduled" in data["metrics"]
    assert "completed" in data["metrics"]
    assert "recentQueue" in data

def test_reports_export_csv():
    payload = {"type": "csv", "filters": {"agencyId": "orgao-ssp"}}
    response = client.post("/api/v1/reports/exports", payload, format="json")
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "csv"
    assert data["status"] == "ready"
    assert "downloadUrl" in data

