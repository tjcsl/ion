from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^$", views.parking_intro_view, name="parking"),
    re_path(r"^/form$", views.parking_form_view, name="parking_form"),
    re_path(r"^/car$", views.parking_car_view, name="parking_car"),
    re_path(r"^/joint$", views.parking_joint_view, name="parking_joint"),
]
