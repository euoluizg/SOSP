from django.urls import re_path
from .views import (
    ServiceGuidanceView,
    ServiceGuidancePdfRequestView,
    GuidancePdfStatusView,
)

urlpatterns = [
    re_path(r"^/services/(?P<service_id>[^/]+)/pdf/?$", ServiceGuidancePdfRequestView.as_view(), name="service-guidance-pdf-request"),
    re_path(r"^/services/(?P<service_id>[^/]+)/?$", ServiceGuidanceView.as_view(), name="service-guidance"),
    re_path(r"^/pdf/(?P<job_id>[^/]+)/?$", GuidancePdfStatusView.as_view(), name="guidance-pdf-status"),
]
