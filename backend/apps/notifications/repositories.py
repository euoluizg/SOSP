import uuid
import datetime
from typing import Any, Dict, List, Optional
from django.conf import settings

class NotificationsInMemoryRepository:
    def __init__(self):
        self._deliveries: List[Dict[str, Any]] = []
        self._preferences: Dict[str, bool] = {}

    def record_delivery(
        self,
        citizen_id: str,
        channel: str,
        template_code: str,
        status: str,
        payload: Dict[str, Any],
        error_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        delivery = {
            "id": f"deliv-{len(self._deliveries) + 1:04d}",
            "citizenId": citizen_id,
            "channel": channel,
            "templateCode": template_code,
            "status": status,
            "payload": payload,
            "errorMessage": error_message,
            "sentAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        self._deliveries.append(delivery)
        return delivery

    def list_deliveries(self, citizen_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if citizen_id:
            return [d for d in self._deliveries if d.get("citizenId") == citizen_id]
        return list(self._deliveries)

    def get_preference(self, citizen_id: str, notification_type: str, channel: str) -> bool:
        key = f"{citizen_id}:{notification_type}:{channel}"
        return self._preferences.get(key, True)

    def set_preference(self, citizen_id: str, notification_type: str, channel: str, is_opt_in: bool) -> None:
        key = f"{citizen_id}:{notification_type}:{channel}"
        self._preferences[key] = is_opt_in


class NotificationsDjangoORMRepository:
    """Implementação real de persistência de notificações via Django ORM (ADR-001)."""

    def record_delivery(
        self,
        citizen_id: str,
        channel: str,
        template_code: str,
        status: str,
        payload: Dict[str, Any],
        error_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        from .models import Delivery
        from django.utils import timezone
        d = Delivery.objects.create(
            citizen_id=citizen_id,
            channel=channel,
            template_code=template_code,
            status=status,
            payload=payload,
            error_message=error_message,
            sent_at=timezone.now() if status == "sent" else None,
        )
        return {
            "id": str(d.id),
            "citizenId": str(d.citizen_id),
            "channel": d.channel,
            "templateCode": d.template_code,
            "status": d.status,
            "sentAt": d.sent_at.isoformat() if d.sent_at else None,
        }

    def list_deliveries(self, citizen_id: Optional[str] = None) -> List[Dict[str, Any]]:
        from .models import Delivery
        qs = Delivery.objects.all().order_by("-created_at")
        if citizen_id:
            qs = qs.filter(citizen_id=citizen_id)
        return [
            {
                "id": str(d.id),
                "citizenId": str(d.citizen_id),
                "channel": d.channel,
                "templateCode": d.template_code,
                "status": d.status,
                "sentAt": d.sent_at.isoformat() if d.sent_at else None,
            }
            for d in qs
        ]

    def get_preference(self, citizen_id: str, notification_type: str, channel: str) -> bool:
        from .models import Preference
        pref = Preference.objects.filter(
            citizen_id=citizen_id,
            notification_type=notification_type,
            channel=channel,
        ).first()
        return pref.is_opt_in if pref else True

    def set_preference(self, citizen_id: str, notification_type: str, channel: str, is_opt_in: bool) -> None:
        from .models import Preference
        from django.utils import timezone
        Preference.objects.update_or_create(
            citizen_id=citizen_id,
            notification_type=notification_type,
            channel=channel,
            defaults={"is_opt_in": is_opt_in, "updated_at": timezone.now()},
        )


_notifications_memory_repository = NotificationsInMemoryRepository()

def get_notifications_repository():
    if getattr(settings, "REPOSITORY_BACKEND", "memory") == "orm":
        return NotificationsDjangoORMRepository()
    return _notifications_memory_repository

class NotificationsRepositoryProxy:
    def __getattr__(self, name):
        repo = get_notifications_repository()
        return getattr(repo, name)

notifications_repository = NotificationsRepositoryProxy()
