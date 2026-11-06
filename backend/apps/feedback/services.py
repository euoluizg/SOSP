import random
import datetime
from typing import Any, Dict, List, Optional
from common.exceptions import ProblemDetailsException
from common.feature_flags import FEATURE_REVIEWS_ENABLED

class FeedbackService:
    _faqs: List[Dict[str, Any]] = [
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

    _questions: List[Dict[str, Any]] = []

    @classmethod
    def list_faqs(cls) -> List[Dict[str, Any]]:
        return cls._faqs

    @classmethod
    def open_question(cls, citizen_name: str, email: str, category: str, subject: str, description: str) -> Dict[str, Any]:
        today_str = datetime.date.today().strftime("%Y%m%d")
        random_suffix = f"{random.randint(1000, 9999)}"
        protocol_number = f"{today_str}-{random_suffix}"

        question_record = {
            "id": f"qst-{len(cls._questions) + 1:04d}",
            "protocolNumber": protocol_number,
            "citizenName": citizen_name,
            "email": email,
            "category": category,
            "subject": subject,
            "description": description,
            "status": "open",
            "createdAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        cls._questions.append(question_record)
        return question_record

    @classmethod
    def submit_review(cls, protocol_number: str, rating: int, comment: Optional[str] = None) -> Dict[str, Any]:
        if not FEATURE_REVIEWS_ENABLED:
            raise ProblemDetailsException(
                detail="O módulo de avaliações e comentários está temporariamente desativado para o MVP (v2.0).",
                title="Recurso desativado",
                status_code=403,
            )
        return {"protocolNumber": protocol_number, "rating": rating, "comment": comment, "recorded": True}

