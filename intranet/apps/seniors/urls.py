from django.conf import settings
from django.urls import path

from . import views

urlpatterns = []

if settings.ENABLE_SENIOR_DESTINATIONS:
    urlpatterns = [path("", views.seniors_home_view, name="seniors"), path("/add", views.seniors_add_view, name="seniors_add")]
