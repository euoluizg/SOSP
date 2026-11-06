import pytest
from rest_framework.test import APIClient

client = APIClient()

def test_get_service_guidance():
    response = client.get("/api/v1/guidance/services/servico-emitir-rg")
    assert response.status_code == 200
    data = response.json()
    assert data["serviceId"] == "servico-emitir-rg"
    assert "steps" in data
    assert "documents" in data

def test_update_guidance_checklist():
    payload = {"checkedItems": ["Certidão de Nascimento", "Comprovante de Residência"]}
    response = client.put("/api/v1/guidance/services/servico-emitir-rg", payload, format="json")
    assert response.status_code == 200
    data = response.json()
    assert data["updated"] is True
    assert len(data["checkedItems"]) == 2

def test_request_and_check_guidance_pdf():
    # Enfileira solicitação
    resp_req = client.post("/api/v1/guidance/services/servico-emitir-rg/pdf")
    assert resp_req.status_code == 202
    job_id = resp_req.json()["jobId"]

    # Consulta status
    resp_status = client.get(f"/api/v1/guidance/pdf/{job_id}")
    assert resp_status.status_code == 200
    assert resp_status.json()["status"] == "completed"

