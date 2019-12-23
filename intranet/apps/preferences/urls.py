from django.urls import re_path

from . import views

urlpatterns = [re_path(r"^$", views.preferences_view, name="preferences"), re_path(r"^/privacy$", views.privacy_options_view, name="privacy_options")]
