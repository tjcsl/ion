from django.urls import path

from . import views

urlpatterns = [
    path("", views.redirect_to_app, name="apps"),
]
