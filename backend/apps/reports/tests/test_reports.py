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
    assert data["contentType"] == "text/csv; charset=utf-8"
    assert data["fileName"] == "relatorio-agendamentos.csv"
    assert data["byteSize"] > 0
    assert "downloadUrl" in data


def test_reports_export_pdf_as_admin(admin_client):
    payload = {"type": "pdf", "filters": {"agencyId": "orgao-ssp"}}
    response = admin_client.post("/api/v1/reports/exports", payload, format="json")
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "pdf"
    assert data["contentType"] == "application/pdf"
    assert data["fileName"] == "relatorio-agendamentos.pdf"
    assert data["byteSize"] > 0


def test_reports_export_rejects_unsupported_format(admin_client):
    payload = {"type": "xlsx", "filters": {}}
    response = admin_client.post("/api/v1/reports/exports", payload, format="json")
    assert response.status_code == 400
    assert response["Content-Type"] == "application/problem+json"


def test_report_exporters_oop_polymorphism():
    """Valida Abstração, Herança e Polimorfismo em ReportExporter / CsvExporter / PdfExporter."""
    from apps.reports.exporters import CsvExporter, PdfExporter, ReportExporter, get_report_exporter

    with pytest.raises(TypeError):
        ReportExporter()  # Classe abstrata não pode ser instanciada diretamente

    sample_summary = {
        "period": {"start": "2026-11-01", "end": "2026-11-30"},
        "metrics": {
            "totalAppointments": 10,
            "scheduled": 4,
            "inProgress": 1,
            "completed": 4,
            "cancelled": 0,
            "noShow": 1,
            "attendanceRate": 40.0,
        },
        "byService": [{"serviceName": "Emitir CIN", "total": 10, "completed": 4, "noShow": 1}],
    }

    csv_exporter = get_report_exporter("csv")
    pdf_exporter = get_report_exporter("pdf")

    assert isinstance(csv_exporter, CsvExporter)
    assert isinstance(pdf_exporter, PdfExporter)
    assert isinstance(csv_exporter, ReportExporter)
    assert isinstance(pdf_exporter, ReportExporter)

    csv_bytes = csv_exporter.export(sample_summary)
    pdf_bytes = pdf_exporter.export(sample_summary)

    assert b"SOSP - Relatorio de Agendamentos" in csv_bytes
    assert b"Emitir CIN" in csv_bytes
    assert pdf_bytes.startswith(b"%PDF-1.4")
    assert b"%%EOF" in pdf_bytes


def test_citizen_cannot_export_reports(auth_client):
    """Cidadão recebe 403 ao tentar exportar relatórios."""
    payload = {"type": "csv", "filters": {"agencyId": "orgao-ssp"}}
    response = auth_client.post("/api/v1/reports/exports", payload, format="json")
    assert response.status_code == 403
    assert response["Content-Type"] == "application/problem+json"
