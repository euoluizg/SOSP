from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import SearchService

class ServicesSearchView(APIView):
    """Busca paginada de serviços públicos com 4 filtros combináveis (RF-06, RN-04, RN-05)."""
    def get(self, request):
        query = request.query_params.get("query") or request.query_params.get("q")
        category = request.query_params.get("category")
        channel = request.query_params.get("channel")
        city = request.query_params.get("city")

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
            page=page,
            page_size=page_size,
        )
        return Response(result, status=status.HTTP_200_OK)

