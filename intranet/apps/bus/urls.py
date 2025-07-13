from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="bus"),
    path("/morning", views.morning, name="morning_bus"),
    path("/afternoon", views.afternoon, name="afternoon_bus"),
    path("/game", views.game, name="bus_game"),
]
