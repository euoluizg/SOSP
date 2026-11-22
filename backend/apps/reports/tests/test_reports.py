import pytest

# Relatórios exigem perfil institucional (servidor ou admin — ADR-003, RS-01).
# Cidadãos recebem 403 Forbidden.


def test_reports_appointments_summary_as_server(server_client):
    response = server_client.get("/api/v1/reports/appointments")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "totalAppointments" in data["metrics"]
    assert "scheduled" in data["metrics"]
    assert "completed" in data["metrics"]
    assert "recentQueue" in data


def test_reports_appointments_summary_as_admin(admin_client):
    response = admin_client.get("/api/v1/reports/appointments")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data


def test_citizen_cannot_access_reports_summary(auth_client):
    """Cidadão recebe 403 ao tentar visualizar relatórios de agendamentos."""
    response = auth_client.get("/api/v1/reports/appointments")
    assert response.status_code == 403
    assert response["Content-Type"] == "application/problem+json"


def test_reports_export_csv_as_server(server_client):
    payload = {"type": "csv", "filters": {"agencyId": "orgao-ssp"}}
    response = server_client.post("/api/v1/reports/exports", payload, format="json")
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "csv"
    assert data["status"] == "ready"
    assert "downloadUrl" in data


def test_citizen_cannot_export_reports(auth_client):
    """Cidadão recebe 403 ao tentar exportar relatórios."""
    payload = {"type": "csv", "filters": {"agencyId": "orgao-ssp"}}
    response = auth_client.post("/api/v1/reports/exports", payload, format="json")
    assert response.status_code == 403
    assert response["Content-Type"] == "application/problem+json"
