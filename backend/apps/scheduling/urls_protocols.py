from django.urls import re_path
from .views import (
    AppointmentCreateListView,
    ProtocolTimelineView,
    ProtocolDocumentsUploadView,
)

urlpatterns = [
    re_path(r"^/?$", AppointmentCreateListView.as_view(), name="protocols-list"),
    re_path(r"^/(?P<protocol_number>[^/]+)/documents/?$", ProtocolDocumentsUploadView.as_view(), name="protocol-documents-upload"),
    re_path(r"^/(?P<protocol_number>[^/]+)(?:/timeline)?/?$", ProtocolTimelineView.as_view(), name="protocol-timeline"),
]
