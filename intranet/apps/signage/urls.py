from django.conf.urls import url
from django.views.generic.base import RedirectView

from . import views

urlpatterns = [
    url(r"^/serviceworker\.js$", RedirectView.as_view(url="/static/signage/serviceworker.js"), name="signage-serviceworker"),
    url(r"^/display/(?P<display_id>[\w_-]+)?$", views.signage_display, name="signage_display"),
    url(r"^/eighth$", views.eighth, name="eighth"),
]
