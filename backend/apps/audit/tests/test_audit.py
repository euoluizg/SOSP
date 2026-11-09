import pytest
from apps.audit.services import AuditService

# Auditoria exige autenticação (REST_FRAMEWORK.DEFAULT_PERMISSION_CLASSES).
# O fixture `auth_client` (backend/conftest.py) autentica via /auth/login.

def test_list_audit_events(auth_client):
    response = auth_client.get("/api/v1/audit/events")
    assert response.status_code == 200
    events = response.json()
    assert isinstance(events, list)
    assert len(events) >= 2
    assert all("action" in e and "targetTable" in e for e in events)

def test_record_audit_event(auth_client):
    evt = AuditService.record_event(
        action="UPDATE",
        target_table="catalogService",
        target_id="servico-emitir-rg",
        actor_id="user-admin-01",
        detail="Atualização de documentação necessária",
    )
    assert evt["id"].startswith("evt-")
    assert evt["action"] == "UPDATE"

    # Confirma listagem
    response = auth_client.get("/api/v1/audit/events")
    assert any(e["id"] == evt["id"] for e in response.json())
