from django.urls import re_path
from .views import (
    AppointmentCreateListView,
    AppointmentDetailView,
    AppointmentCancelView,
    AppointmentByProtocolView,
)

urlpatterns = [
    re_path(r"^/?$", AppointmentCreateListView.as_view(), name="appointments-list-create"),
    re_path(r"^/by-protocol/(?P<protocol_number>[^/]+)/?$", AppointmentByProtocolView.as_view(), name="appointment-by-protocol"),
    re_path(r"^/(?P<appointment_id>[^/]+)/cancel/?$", AppointmentCancelView.as_view(), name="appointment-cancel"),
    re_path(r"^/(?P<appointment_id>[^/]+)/?$", AppointmentDetailView.as_view(), name="appointment-detail"),
]
