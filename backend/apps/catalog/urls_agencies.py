from django.urls import re_path
from .views import AgenciesListView, AgencyDetailView

urlpatterns = [
    re_path(r"^/?$", AgenciesListView.as_view(), name="agencies-list"),
    re_path(r"^/(?P<agency_id>[^/]+)/?$", AgencyDetailView.as_view(), name="agency-detail"),
]
