from django.urls import path

from . import views

urlpatterns = [
    path("", views.print_view, name="printing"),
    path("/banned", views.printing_banned, name="printing_banned"),
]
