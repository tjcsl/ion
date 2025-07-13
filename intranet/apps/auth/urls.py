from django.urls import path

from . import views

urlpatterns = [
    path("", views.index_view, name="index"),
    path("login", views.LoginView.as_view(), name="login"),
    path("logout", views.logout_view, name="logout"),
    path("about", views.about_view, name="about"),
    path("reauthenticate", views.reauthentication_view, name="reauth"),
    path("reset_password", views.reset_password_view, name="reset_password"),
]
