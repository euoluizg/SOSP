from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import GuidanceService

class ServiceGuidanceView(APIView):
    def get(self, request, service_id):
        result = GuidanceService.get_guidance(service_id)
        return Response(result, status=status.HTTP_200_OK)

    def put(self, request, service_id):
        checked_items = request.data.get("checkedItems", [])
        result = GuidanceService.update_checklist(service_id, checked_items)
        return Response(result, status=status.HTTP_200_OK)

class ServiceGuidancePdfRequestView(APIView):
    def post(self, request, service_id):
        result = GuidanceService.request_pdf(service_id)
        return Response(result, status=status.HTTP_202_ACCEPTED)

class GuidancePdfStatusView(APIView):
    def get(self, request, job_id):
        result = GuidanceService.get_pdf_job(job_id)
        return Response(result, status=status.HTTP_200_OK)

