from django.urls import path, re_path
from apps.search.views import ServicesSearchView
from apps.catalog.views import (
    ServiceDetailView,
    ServiceStepsView,
    ServiceDocumentsView,
)

urlpatterns = [
    re_path(r"^/?$", ServicesSearchView.as_view(), name="services-search"),
    re_path(r"^/(?P<service_id>[^/]+)/steps/?$", ServiceStepsView.as_view(), name="service-steps"),
    re_path(r"^/(?P<service_id>[^/]+)/documents/?$", ServiceDocumentsView.as_view(), name="service-documents"),
    re_path(r"^/(?P<service_id>[^/]+)/?$", ServiceDetailView.as_view(), name="service-detail"),
]
