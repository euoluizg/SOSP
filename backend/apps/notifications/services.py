import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    def send_transactional_email(to_email: str, subject: str, message: str) -> Dict[str, Any]:
        """Simula o envio de e-mail transacional (Mailpit/Console)."""
        logger.info(f"[Email Simulado] Para: {to_email} | Assunto: {subject} | Mensagem: {message[:60]}...")
        return {
            "status": "sent",
            "to": to_email,
            "subject": subject,
        }

