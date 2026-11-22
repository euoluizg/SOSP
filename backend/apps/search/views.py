from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from common.security.permissions import IsManagerUser
from common.exceptions import ProblemDetailsException
from apps.catalog.serializers import ServiceCreateSerializer
from apps.catalog.services import CatalogService
from .services import SearchService


class ServicesSearchView(APIView):
    """Busca paginada de serviços públicos com 4 filtros combináveis (RF-06, RN-04, RN-05) e criação administrativa."""

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsManagerUser()]
        return [AllowAny()]

    def get(self, request):
        query = request.query_params.get("query") or request.query_params.get("q")
        category = request.query_params.get("category")
        channel = request.query_params.get("channel")
        city = request.query_params.get("city")
        agency_id = request.query_params.get("agencyId")

        try:
            page = int(request.query_params.get("page", 1))
        except ValueError:
            page = 1

        try:
            page_size = int(request.query_params.get("pageSize", 10))
        except ValueError:
            page_size = 10

        result = SearchService.search_services(
            query=query,
            category=category,
            channel=channel,
            city=city,
            agency_id=agency_id,
            page=page,
            page_size=page_size,
        )
        return Response(result, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ServiceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if getattr(user, "role", "") in ("gestor", "manager"):
            user_agency = getattr(user, "agency_id", None)
            if not user_agency or str(user_agency) != str(serializer.validated_data["agencyId"]):
                raise ProblemDetailsException(
                    detail="Você não possui autorização para criar serviços fora do seu órgão.",
                    title="Acesso Não Autorizado",
                    status_code=403,
                )
        created = CatalogService.create_service(serializer.validated_data, user=user)
        return Response(created, status=status.HTTP_201_CREATED)

