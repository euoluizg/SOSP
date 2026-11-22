from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .services import GuidanceService

class ServiceGuidanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, service_id):
        citizen_id = str(request.user.id) if request.user and getattr(request.user, "is_authenticated", False) else "citizen-001"
        result = GuidanceService.get_guidance(service_id, citizen_id=citizen_id)
        return Response(result, status=status.HTTP_200_OK)

    def put(self, request, service_id):
        citizen_id = str(request.user.id) if request.user and getattr(request.user, "is_authenticated", False) else "citizen-001"
        checked_items = request.data.get("checkedItems", [])
        result = GuidanceService.update_checklist(service_id, checked_items, citizen_id=citizen_id)
        return Response(result, status=status.HTTP_200_OK)

class ServiceGuidancePdfRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, service_id):
        citizen_id = str(request.user.id) if request.user and getattr(request.user, "is_authenticated", False) else "citizen-001"
        result = GuidanceService.request_pdf(service_id, citizen_id=citizen_id)
        return Response(result, status=status.HTTP_202_ACCEPTED)

class GuidancePdfStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        result = GuidanceService.get_pdf_job(job_id)
        return Response(result, status=status.HTTP_200_OK)

