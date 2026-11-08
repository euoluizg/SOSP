from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import (
    CitizenRegisterSerializer,
    CitizenLoginSerializer,
    PasswordRecoveryRequestSerializer,
    PasswordResetSerializer,
)
from .services import AccountService
from .repositories import citizen_repository
from common.exceptions import ProblemDetailsException

class RegisterView(APIView):
    def post(self, request):
        serializer = CitizenRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        citizen = AccountService.register_citizen(serializer.validated_data)
        return Response(citizen, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    def post(self, request):
        serializer = CitizenLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = AccountService.login_citizen(
            cpf=serializer.validated_data["cpf"],
            password=serializer.validated_data["password"],
        )
        return Response(result, status=status.HTTP_200_OK)

class LogoutView(APIView):
    def post(self, request):
        auth_header = request.headers.get("Authorization", "")
        token = ""
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
        result = AccountService.logout_citizen(token)
        return Response(result, status=status.HTTP_200_OK)

class PasswordRecoveryView(APIView):
    def post(self, request):
        serializer = PasswordRecoveryRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = AccountService.request_password_recovery(serializer.validated_data["cpf"])
        return Response(result, status=status.HTTP_200_OK)

class PasswordResetView(APIView):
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = AccountService.reset_password(
            cpf=serializer.validated_data["cpf"],
            code=serializer.validated_data["code"],
            new_password=serializer.validated_data["newPassword"],
        )
        return Response(result, status=status.HTTP_200_OK)

class CitizenMeView(APIView):
    def get(self, request):
        if request.user and getattr(request.user, "is_authenticated", False):
            citizen_id = str(request.user.id)
        else:
            citizen_id = "citizen-001"
        citizen = citizen_repository.get_by_id(citizen_id)
        if not citizen:
            raise ProblemDetailsException(detail="Perfil não encontrado.", status_code=404)
        safe_copy = dict(citizen)
        safe_copy.pop("passwordHash", None)
        return Response(safe_copy, status=status.HTTP_200_OK)

