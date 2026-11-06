from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import FeedbackService
from common.exceptions import ProblemDetailsException

class FaqListView(APIView):
    def get(self, request):
        faqs = FeedbackService.list_faqs()
        return Response(faqs, status=status.HTTP_200_OK)

class QuestionCreateView(APIView):
    def post(self, request):
        citizen_name = request.data.get("citizenName") or request.data.get("name")
        email = request.data.get("email")
        category = request.data.get("category", "Geral")
        subject = request.data.get("subject", "Dúvida Geral")
        description = request.data.get("description") or request.data.get("message")

        if not citizen_name or not email or not description:
            raise ProblemDetailsException(
                detail="Nome, e-mail e descrição são campos obrigatórios para abertura de dúvida.",
                status_code=400,
            )

        question = FeedbackService.open_question(
            citizen_name=citizen_name,
            email=email,
            category=category,
            subject=subject,
            description=description,
        )
        return Response(question, status=status.HTTP_201_CREATED)

class ReviewSubmitView(APIView):
    def post(self, request, protocol_number):
        rating = request.data.get("rating", 5)
        comment = request.data.get("comment")
        result = FeedbackService.submit_review(protocol_number, rating, comment)
        return Response(result, status=status.HTTP_201_CREATED)

