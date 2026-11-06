from django.urls import re_path
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    PasswordRecoveryView,
    PasswordResetView,
)

urlpatterns = [
    re_path(r"^register/?$", RegisterView.as_view(), name="auth-register"),
    re_path(r"^login/?$", LoginView.as_view(), name="auth-login"),
    re_path(r"^logout/?$", LogoutView.as_view(), name="auth-logout"),
    re_path(r"^recover-password/?$", PasswordRecoveryView.as_view(), name="auth-recover-password"),
    re_path(r"^reset-password/?$", PasswordResetView.as_view(), name="auth-reset-password"),
]
