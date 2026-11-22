from typing import Any, Dict, List, Optional
from .repositories import audit_repository

class AuditService:
    @classmethod
    def record_event(
        cls,
        action: str,
        target_table: str,
        target_id: str,
        actor_id: Optional[str] = None,
        actor_user_id: Optional[str] = None,
        detail: str = "",
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
        ip_address: str = "127.0.0.1",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        actual_actor_id = actor_user_id or actor_id or "system"
        if not detail and after_state:
            detail = f"Operação {action} em {target_table} ID {target_id}"
        return audit_repository.record_event({
            "action": action,
            "target_table": target_table,
            "target_id": target_id,
            "actor_id": actual_actor_id,
            "detail": detail,
            "before_state": before_state,
            "after_state": after_state,
            "ip_address": ip_address,
        })

    @classmethod
    def list_events(cls) -> List[Dict[str, Any]]:
        return audit_repository.list_events()
