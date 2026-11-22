from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from common.security.permissions import IsAdminUser
from .services import AuditService


class AuditEventsListView(APIView):
    """
    Lista eventos da trilha imutável de auditoria.
    Restrito exclusivamente a administradores do sistema (ADR-003, RS-03).
    """

    permission_classes = [IsAdminUser]

    def get(self, request):
        events = AuditService.list_events()
        return Response(events, status=status.HTTP_200_OK)
