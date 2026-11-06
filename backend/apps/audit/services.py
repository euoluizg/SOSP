import datetime
from typing import Any, Dict, List, Optional

class AuditService:
    _events: List[Dict[str, Any]] = [
        {
            "id": "evt-001",
            "actorUserId": "user-admin-01",
            "actorName": "Administrador Geral",
            "action": "CREATE",
            "targetTable": "catalogService",
            "targetId": "servico-emitir-rg",
            "ipAddress": "127.0.0.1",
            "createdAt": "2026-11-01T08:00:00Z",
            "detail": "Publicação da versão 1.0 do serviço CIN",
        },
        {
            "id": "evt-002",
            "actorUserId": "citizen-001",
            "actorName": "Cidadão de Testes",
            "action": "CREATE",
            "targetTable": "schedulingAppointment",
            "targetId": "appt-001",
            "ipAddress": "187.19.20.1",
            "createdAt": "2026-11-05T10:00:00Z",
            "detail": "Reserva de slot presencial para CIN",
        },
    ]

    @classmethod
    def record_event(cls, action: str, target_table: str, target_id: str, actor_id: str = "system", detail: str = "") -> Dict[str, Any]:
        event = {
            "id": f"evt-{len(cls._events) + 1:03d}",
            "actorUserId": actor_id,
            "action": action,
            "targetTable": target_table,
            "targetId": target_id,
            "detail": detail,
            "ipAddress": "127.0.0.1",
            "createdAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        cls._events.insert(0, event)
        return event

    @classmethod
    def list_events(cls) -> List[Dict[str, Any]]:
        return list(cls._events)

