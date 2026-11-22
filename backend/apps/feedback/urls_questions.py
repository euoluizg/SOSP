from django.urls import re_path
from .views import QuestionCreateView

urlpatterns = [
    re_path(r"^/?$", QuestionCreateView.as_view(), name="questions-create"),
]
