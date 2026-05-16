from django.urls import path

from . import views

urlpatterns = [
    path("", views.wrapped_view, name="wrapped"),
]
