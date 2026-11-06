import pytest
import re
from rest_framework.test import APIClient
from apps.scheduling.services import SchedulingService

client = APIClient()

def test_get_slots_30_minutes_interval():
    # Segunda-feira útil
    slots = SchedulingService.get_slots_for_unit("unidade-centro", "2026-11-09")
    assert len(slots) > 0
    for s in slots:
        start_h, start_m = map(int, s["startsAt"].split(":"))
        end_h, end_m = map(int, s["endsAt"].split(":"))
        duration = (end_h * 60 + end_m) - (start_h * 60 + start_m)
        assert duration == 30, f"Slot {s['startsAt']}-{s['endsAt']} deve ter 30 minutos (RN-18)"

def test_slots_weekend_closed():
    # Domingo (2026-11-15) - RN-19
    slots = SchedulingService.get_slots_for_unit("unidade-centro", "2026-11-15")
    assert len(slots) == 0

def test_create_appointment_and_protocol_format():
    payload = {
        "serviceId": "servico-isencao-ipva",
        "unitId": "unidade-centro",
        "scheduledDate": "2026-11-20",
        "scheduledTime": "10:30",
        "citizenId": "citizen-002",
    }
    response = client.post("/api/v1/appointments/", payload, format="json")
    assert response.status_code == 201
    data = response.json()
    assert "protocolNumber" in data
    # Protocolo no formato AAAAMMDD-XXXX (RN-20)
    assert re.match(r"^\d{8}-\d{4}$", data["protocolNumber"])
    assert data["status"] == "scheduled"

def test_cancel_appointment():
    # Cria agendamento para cancelamento
    appt = SchedulingService.create_appointment(
        citizen_id="citizen-cancel-test",
        service_id="servico-passe-livre",
        unit_id="unidade-centro",
        scheduled_date="2026-11-25",
        scheduled_time="14:00",
    )
    appt_id = appt["id"]

    response = client.post(f"/api/v1/appointments/{appt_id}/cancel", {"reason": "Imprevisto pessoal"}, format="json")
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"

def test_attachment_upload_size_limit():
    protocol = "20261105-1042"
    # Arquivo dentro do limite de 10 MB
    resp_ok = client.post(
        f"/api/v1/protocols/{protocol}/documents",
        {"fileName": "rg_frente_verso.pdf", "sizeMb": 2.5},
        format="json",
    )
    assert resp_ok.status_code == 201

    # Arquivo acima do limite de 10 MB (RS-04)
    resp_err = client.post(
        f"/api/v1/protocols/{protocol}/documents",
        {"fileName": "arquivo_gigante.pdf", "sizeMb": 15.0},
        format="json",
    )
    assert resp_err.status_code == 400
    assert "10 mb" in resp_err.json()["detail"].lower()

