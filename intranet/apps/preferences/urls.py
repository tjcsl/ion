from django.urls import path

from . import views

urlpatterns = [path("", views.preferences_view, name="preferences"), path("/privacy", views.privacy_options_view, name="privacy_options")]
