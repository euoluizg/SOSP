import logging
from typing import Dict, Any, Optional
from .repositories import notifications_repository

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    def send_transactional_email(to_email: str, subject: str, message: str, citizen_id: Optional[str] = None) -> Dict[str, Any]:
        """Simula o envio de e-mail transacional (Mailpit/Console) e registra no repositório."""
        logger.info(f"[Email Simulado] Para: {to_email} | Assunto: {subject} | Mensagem: {message[:60]}...")

        record = notifications_repository.record_delivery(
            citizen_id=citizen_id or "citizen-001",
            channel="email",
            template_code="TRANSACTIONAL_EMAIL",
            status="sent",
            payload={"to": to_email, "subject": subject, "preview": message[:100]},
        )
        return {
            "status": "sent",
            "to": to_email,
            "subject": subject,
            "deliveryId": record.get("id"),
        }
