from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^$", views.logs_view, name="logs"),
    re_path(r"^/request/(?P<request_id>\d+)$", views.request_view, name="request"),
]
