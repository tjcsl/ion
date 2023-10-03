from django.conf import settings
from django.urls import re_path

from . import views

urlpatterns = []

if settings.ENABLE_SENIOR_DESTINATIONS:
    urlpatterns = [re_path(r"^$", views.seniors_home_view, name="seniors"), re_path(r"^/add$", views.seniors_add_view, name="seniors_add")]
