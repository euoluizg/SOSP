import uuid
import datetime
from typing import Any, Dict, List, Optional
from django.conf import settings

class AuditInMemoryRepository:
    def __init__(self):
        self._events: List[Dict[str, Any]] = [
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

    def record_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        evt_id = f"evt-{len(self._events) + 1:03d}"
        event = {
            "id": evt_id,
            "actorUserId": event_data.get("actor_id", "system"),
            "action": event_data.get("action", "UNKNOWN"),
            "targetTable": event_data.get("target_table", ""),
            "targetId": event_data.get("target_id", ""),
            "detail": event_data.get("detail", ""),
            "ipAddress": event_data.get("ip_address", "127.0.0.1"),
            "createdAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        self._events.insert(0, event)
        return event

    def list_events(self) -> List[Dict[str, Any]]:
        return list(self._events)


class AuditDjangoORMRepository:
    """Implementação real de persistência de trilha de auditoria via Django ORM (RN-39, ADR-001)."""

    def record_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        from .models import AuditEvent
        raw_actor_id = event_data.get("actor_id")
        actor_id = None
        actor_type = event_data.get("actor_type") or "servant"
        if raw_actor_id:
            if str(raw_actor_id).startswith("citizen-"):
                actor_type = "citizen"
            elif str(raw_actor_id) in ("system", "anonymous"):
                actor_type = str(raw_actor_id)
            try:
                actor_id = uuid.UUID(str(raw_actor_id))
            except Exception:
                actor_id = None
        elif actor_type not in ("citizen", "servant", "system", "anonymous"):
            actor_type = "system"

        if actor_type not in ("citizen", "servant", "system", "anonymous"):
            actor_type = "servant"

        raw_target_id = event_data.get("target_id")
        entity_id = None
        if raw_target_id:
            try:
                entity_id = uuid.UUID(str(raw_target_id))
            except Exception:
                entity_id = None

        detail = event_data.get("detail", "")
        after_data = event_data.get("after_state") or ({"detail": detail} if detail else {})
        before_data = event_data.get("before_state")

        evt = AuditEvent.objects.create(
            actor_type=actor_type,
            actor_id=actor_id,
            action=event_data.get("action", "UNKNOWN"),
            entity_type=event_data.get("target_table", "general"),
            entity_id=entity_id,
            before_data=before_data,
            after_data=after_data,
            ip_address=event_data.get("ip_address", "127.0.0.1"),
        )
        return {
            "id": f"evt-{str(evt.id)[:8]}",
            "actorUserId": str(raw_actor_id or "system"),
            "action": evt.action,
            "targetTable": evt.entity_type,
            "targetId": str(raw_target_id or ""),
            "detail": detail,
            "ipAddress": evt.ip_address,
            "createdAt": evt.created_at.isoformat(),
        }

    def list_events(self) -> List[Dict[str, Any]]:
        from .models import AuditEvent
        qs = AuditEvent.objects.all().order_by("-created_at")[:100]
        return [
            {
                "id": f"evt-{str(e.id)[:8]}",
                "actorUserId": str(e.actor_id or "system"),
                "action": e.action,
                "targetTable": e.entity_type,
                "targetId": str(e.entity_id or ""),
                "detail": (e.after_data or {}).get("detail", ""),
                "ipAddress": e.ip_address or "127.0.0.1",
                "createdAt": e.created_at.isoformat(),
            }
            for e in qs
        ]


_audit_memory_repository = AuditInMemoryRepository()

def get_audit_repository():
    if getattr(settings, "REPOSITORY_BACKEND", "memory") == "orm":
        return AuditDjangoORMRepository()
    return _audit_memory_repository

class AuditRepositoryProxy:
    def __getattr__(self, name):
        repo = get_audit_repository()
        return getattr(repo, name)

audit_repository = AuditRepositoryProxy()
