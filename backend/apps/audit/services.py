from typing import Any, Dict, List, Optional
from .repositories import audit_repository

class AuditService:
    @classmethod
    def record_event(cls, action: str, target_table: str, target_id: str, actor_id: str = "system", detail: str = "") -> Dict[str, Any]:
        return audit_repository.record_event({
            "action": action,
            "target_table": target_table,
            "target_id": target_id,
            "actor_id": actor_id,
            "detail": detail,
            "ip_address": "127.0.0.1",
        })

    @classmethod
    def list_events(cls) -> List[Dict[str, Any]]:
        return audit_repository.list_events()
