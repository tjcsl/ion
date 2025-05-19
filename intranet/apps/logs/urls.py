from django.urls import path

from . import views

urlpatterns = [
    path("", views.logs_view, name="logs"),
    path("/request/<int:request_id>", views.request_view, name="request"),
]
