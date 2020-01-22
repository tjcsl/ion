from django.urls import re_path
from django.views.generic.base import RedirectView

from . import views

urlpatterns = [
    re_path(r"^/serviceworker\.js$", RedirectView.as_view(url="/static/signage/serviceworker.js"), name="signage-serviceworker"),
    # This MUST match the SignageConsumer entry in intranet/routing.py
    re_path(r"^/display/(?P<display_id>[\w_-]+)?$", views.signage_display, name="signage_display"),
    re_path(r"^/eighth$", views.eighth, name="eighth"),
    re_path(r"^/prometheus-metrics$", views.prometheus_metrics, name="prometheus_metrics"),
]
