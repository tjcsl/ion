from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^$", views.index_view, name="index"),
    re_path(r"^login$", views.LoginView.as_view(), name="login"),
    re_path(r"^logout$", views.logout_view, name="logout"),
    re_path(r"^about$", views.about_view, name="about"),
    re_path(r"^reauthenticate$", views.reauthentication_view, name="reauth"),
    re_path(r"^reset_password$", views.reset_password_view, name="reset_password"),
]
