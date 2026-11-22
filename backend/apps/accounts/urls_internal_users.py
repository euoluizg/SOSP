from django.urls import re_path
from .views import InternalUsersListCreateView, InternalUserDetailView

urlpatterns = [
    re_path(r"^/?$", InternalUsersListCreateView.as_view(), name="internal-users-list-create"),
    re_path(r"^/(?P<user_id>[^/]+)/?$", InternalUserDetailView.as_view(), name="internal-user-detail"),
]
