from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from common.security.permissions import IsManagerUser
from common.exceptions import ProblemDetailsException
from .services import CatalogService
from .serializers import AgencyUpdateSerializer

class AgenciesListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        agencies = CatalogService.list_agencies()
        return Response(agencies, status=status.HTTP_200_OK)

class AgencyDetailView(APIView):
    def get_permissions(self):
        if self.request.method in ("PATCH", "PUT"):
            return [IsAuthenticated(), IsManagerUser()]
        return [AllowAny()]

    def get(self, request, agency_id):
        agency = CatalogService.get_agency_or_404(agency_id)
        return Response(agency, status=status.HTTP_200_OK)

    def patch(self, request, agency_id):
        # Validação de escopo de permissão: gestor institucional só pode editar seu próprio órgão
        user = request.user
        role = getattr(user, "role", "")
        if role in ("gestor", "manager"):
            user_agency = getattr(user, "agency_id", None)
            if not user_agency or str(user_agency) != str(agency_id):
                raise ProblemDetailsException(
                    detail="Você não possui autorização para editar órgãos fora de sua instituição de lotação.",
                    title="Acesso Não Autorizado",
                    status_code=403,
                )

        serializer = AgencyUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        updated = CatalogService.update_agency(
            agency_id=agency_id,
            data=serializer.validated_data,
            user=user,
        )
        return Response(updated, status=status.HTTP_200_OK)

    def put(self, request, agency_id):
        return self.patch(request, agency_id)

class UnitsListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        agency_id = request.query_params.get("agencyId")
        units = CatalogService.list_units(agency_id=agency_id)
        return Response(units, status=status.HTTP_200_OK)

class ServiceDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, service_id):
        service = CatalogService.get_service_or_404(service_id)
        return Response(service, status=status.HTTP_200_OK)

class ServiceStepsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, service_id):
        service = CatalogService.get_service_or_404(service_id)
        return Response(service.get("steps", []), status=status.HTTP_200_OK)

class ServiceDocumentsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, service_id):
        service = CatalogService.get_service_or_404(service_id)
        return Response(service.get("documents", []), status=status.HTTP_200_OK)

class CategoriesListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        categories = CatalogService.list_categories()
        return Response(categories, status=status.HTTP_200_OK)
