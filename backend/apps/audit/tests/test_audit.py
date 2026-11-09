import pytest
from apps.audit.services import AuditService

# Auditoria exige privilégio de Administrador (ADR-003, RS-03).
# Cidadãos e servidores devem receber 403 Forbidden.


def test_list_audit_events_as_admin(admin_client):
    response = admin_client.get("/api/v1/audit/events")
    assert response.status_code == 200
    events = response.json()
    assert isinstance(events, list)
    assert len(events) >= 2
    assert all("action" in e and "targetTable" in e for e in events)


def test_citizen_cannot_access_audit_events(auth_client):
    """Cidadão recebe 403 ao tentar visualizar eventos de auditoria."""
    response = auth_client.get("/api/v1/audit/events")
    assert response.status_code == 403
    assert response["Content-Type"] == "application/problem+json"


def test_server_cannot_access_audit_events(server_client):
    """Servidor público recebe 403 ao tentar visualizar eventos de auditoria."""
    response = server_client.get("/api/v1/audit/events")
    assert response.status_code == 403
    assert response["Content-Type"] == "application/problem+json"


def test_record_audit_event(admin_client):
    evt = AuditService.record_event(
        action="UPDATE",
        target_table="catalogService",
        target_id="servico-emitir-rg",
        actor_id="user-admin-01",
        detail="Atualização de documentação necessária",
    )
    assert evt["id"].startswith("evt-")
    assert evt["action"] == "UPDATE"

    # Confirma listagem pelo admin
    response = admin_client.get("/api/v1/audit/events")
    assert response.status_code == 200
    assert any(e["id"] == evt["id"] for e in response.json())
