from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^$", views.redirect_to_app, name="apps"),
]
