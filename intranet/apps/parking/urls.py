from django.urls import path

from . import views

urlpatterns = [
    path("", views.parking_intro_view, name="parking"),
    path("/form", views.parking_form_view, name="parking_form"),
    path("/car", views.parking_car_view, name="parking_car"),
    path("/joint", views.parking_joint_view, name="parking_joint"),
]
