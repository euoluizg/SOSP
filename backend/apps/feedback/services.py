import random
import datetime
from typing import Any, Dict, List, Optional
from common.exceptions import ProblemDetailsException
from common.feature_flags import FEATURE_REVIEWS_ENABLED
from .repositories import feedback_repository

class FeedbackService:
    @classmethod
    def list_faqs(cls) -> List[Dict[str, Any]]:
        return feedback_repository.list_faqs()

    @classmethod
    def open_question(cls, citizen_name: str, email: str, category: str, subject: str, description: str) -> Dict[str, Any]:
        today_str = datetime.date.today().strftime("%Y%m%d")
        random_suffix = f"{random.randint(1000, 9999)}"
        protocol_number = f"{today_str}-{random_suffix}"

        question_record = {
            "id": f"qst-{random.randint(1000, 9999):04d}",
            "protocolNumber": protocol_number,
            "citizenName": citizen_name,
            "email": email,
            "category": category,
            "subject": subject,
            "description": description,
            "status": "open",
            "createdAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        return feedback_repository.create_question(question_record)

    @classmethod
    def submit_review(cls, protocol_number: str, rating: int, comment: Optional[str] = None) -> Dict[str, Any]:
        if not FEATURE_REVIEWS_ENABLED:
            raise ProblemDetailsException(
                detail="O módulo de avaliações e comentários está temporariamente desativado para o MVP (v2.0).",
                title="Recurso desativado",
                status_code=403,
            )
        review_data = {
            "protocolNumber": protocol_number,
            "rating": rating,
            "comment": comment,
        }
        return feedback_repository.create_review(review_data)
