from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import CatalogService

class AgenciesListView(APIView):
    def get(self, request):
        agencies = CatalogService.list_agencies()
        return Response(agencies, status=status.HTTP_200_OK)

class UnitsListView(APIView):
    def get(self, request):
        agency_id = request.query_params.get("agencyId")
        units = CatalogService.list_units(agency_id=agency_id)
        return Response(units, status=status.HTTP_200_OK)

class ServiceDetailView(APIView):
    def get(self, request, service_id):
        service = CatalogService.get_service_or_404(service_id)
        return Response(service, status=status.HTTP_200_OK)

class ServiceStepsView(APIView):
    def get(self, request, service_id):
        service = CatalogService.get_service_or_404(service_id)
        return Response(service.get("steps", []), status=status.HTTP_200_OK)

class ServiceDocumentsView(APIView):
    def get(self, request, service_id):
        service = CatalogService.get_service_or_404(service_id)
        return Response(service.get("documents", []), status=status.HTTP_200_OK)

class CategoriesListView(APIView):
    def get(self, request):
        categories = CatalogService.list_categories()
        return Response(categories, status=status.HTTP_200_OK)

