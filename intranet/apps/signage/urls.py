from django.conf.urls import url
from django.views.generic.base import TemplateView

from . import views

urlpatterns = [
    url(r"^/serviceworker\.js$", TemplateView.as_view(template_name="signage/serviceworker.js", content_type="text/javascript"),
        name="signage-serviceworker"),
    url(r"^/display/(?P<display_id>[\w_-]+)?$", views.signage_display, name="signage_display"),
    url(r"^/page/eighth(?:/(?P<block_id>\d+))?$", views.eighth_signage, name="eighth_signage"),
]
