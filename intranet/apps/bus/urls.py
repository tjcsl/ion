from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^$", views.home, name="bus"),
    re_path(r"^/morning$", views.morning, name="morning_bus"),
    re_path(r"^/afternoon$", views.afternoon, name="afternoon_bus"),
]
