import uuid
import datetime
from typing import Any, Dict, List, Optional
from django.conf import settings

class FeedbackInMemoryRepository:
    def __init__(self):
        self._faqs: List[Dict[str, Any]] = [
            {
                "id": "faq-01",
                "category": "Geral",
                "question": "Como agendar um atendimento no SOSP?",
                "answer": "Basta acessar o portal, buscar o serviço desejado, escolher a unidade de atendimento, a data e o horário disponível em slots de 30 minutos. Ao confirmar, seu protocolo AAAAMMDD-XXXX será gerado.",
            },
            {
                "id": "faq-02",
                "category": "Documentos",
                "question": "O que fazer se eu esquecer algum documento no dia do atendimento?",
                "answer": "Caso falte algum documento obrigatório, o servidor poderá orientá-lo a anexar o documento complementar pelo portal em até 5 dias úteis ou realizar uma nova remarcação.",
            },
            {
                "id": "faq-03",
                "category": "Gov.br",
                "question": "Por que o botão Entrar com Gov.br abre uma mensagem de atualização?",
                "answer": "A integração oficial federada com a conta Gov.br está planejada para a versão 2.0 do SOSP. No momento, todos os cidadãos acessam utilizando CPF e senha locais com segurança criptográfica Argon2id.",
            },
        ]
        self._questions: List[Dict[str, Any]] = []
        self._reviews: List[Dict[str, Any]] = []

    def list_faqs(self) -> List[Dict[str, Any]]:
        return list(self._faqs)

    def create_question(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        self._questions.append(question_data)
        return question_data

    def list_questions(self) -> List[Dict[str, Any]]:
        return list(self._questions)

    def create_review(self, review_data: Dict[str, Any]) -> Dict[str, Any]:
        self._reviews.append(review_data)
        return review_data

    def list_reviews(self) -> List[Dict[str, Any]]:
        return list(self._reviews)


class FeedbackDjangoORMRepository:
    """Implementação real de persistência de feedback via Django ORM (ADR-001)."""

    def __init__(self):
        # FAQs são conteúdo estático gerenciado no portal / CMS do MVP
        self._faqs = FeedbackInMemoryRepository()._faqs

    def list_faqs(self) -> List[Dict[str, Any]]:
        return self._faqs

    def create_question(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        from .models import Question
        from apps.scheduling.models import Protocol
        from apps.accounts.models import Citizen
        from apps.catalog.models import Service

        protocol_number = question_data.get("protocolNumber")
        protocol = Protocol.objects.filter(protocol_number=protocol_number).first()
        citizen = None
        if protocol and protocol.citizen_id:
            citizen = Citizen.objects.filter(id=protocol.citizen_id).first()
        if not citizen:
            citizen = Citizen.objects.first()

        service = None
        if protocol and protocol.service_id:
            service = Service.objects.filter(id=protocol.service_id).first()

        if protocol and citizen:
            q = Question.objects.create(
                protocol=protocol,
                citizen=citizen,
                service=service,
                subject=question_data.get("subject", "Dúvida"),
                message=question_data.get("description", ""),
                attachment_url=question_data.get("attachmentUrl"),
            )
            return {
                "id": str(q.id),
                "protocolNumber": protocol.protocol_number,
                "citizenName": question_data.get("citizenName", ""),
                "email": question_data.get("email", ""),
                "category": question_data.get("category", ""),
                "subject": q.subject,
                "description": q.message,
                "status": "open",
                "createdAt": q.created_at.isoformat(),
            }
        return question_data

    def list_questions(self) -> List[Dict[str, Any]]:
        from .models import Question
        qs = Question.objects.select_related("protocol", "citizen").order_by("-created_at")
        return [
            {
                "id": str(q.id),
                "protocolNumber": q.protocol.protocol_number if q.protocol else "",
                "citizenName": q.citizen.full_name if q.citizen else "",
                "subject": q.subject,
                "description": q.message,
                "answer": q.answer or "",
                "createdAt": q.created_at.isoformat(),
            }
            for q in qs
        ]

    def create_review(self, review_data: Dict[str, Any]) -> Dict[str, Any]:
        from .models import Review
        from apps.scheduling.models import Protocol
        protocol_number = review_data.get("protocolNumber")
        protocol = Protocol.objects.filter(protocol_number=protocol_number).first()
        if protocol:
            r = Review.objects.create(
                protocol=protocol,
                citizen_id=protocol.citizen_id,
                service_id=protocol.service_id,
                unit_id=protocol.unit_id,
                rating=review_data.get("rating", 5),
                review_comment=review_data.get("comment"),
            )
            return {
                "id": str(r.id),
                "protocolNumber": protocol_number,
                "rating": r.rating,
                "comment": r.review_comment,
                "recorded": True,
            }
        return review_data

    def list_reviews(self) -> List[Dict[str, Any]]:
        from .models import Review
        qs = Review.objects.order_by("-created_at")
        return [
            {
                "id": str(r.id),
                "rating": r.rating,
                "comment": r.review_comment,
                "createdAt": r.created_at.isoformat(),
            }
            for r in qs
        ]


_feedback_memory_repository = FeedbackInMemoryRepository()

def get_feedback_repository():
    if getattr(settings, "REPOSITORY_BACKEND", "memory") == "orm":
        return FeedbackDjangoORMRepository()
    return _feedback_memory_repository

class FeedbackRepositoryProxy:
    def __getattr__(self, name):
        repo = get_feedback_repository()
        return getattr(repo, name)

feedback_repository = FeedbackRepositoryProxy()
