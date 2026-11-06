from django.urls import re_path
from .views import FaqListView, ReviewSubmitView

urlpatterns = [
    re_path(r"^/faq/?$", FaqListView.as_view(), name="feedback-faq"),
    re_path(r"^/reviews/(?P<protocol_number>[^/]+)/?$", ReviewSubmitView.as_view(), name="feedback-review-submit"),
]
