from django.urls import path

from . import views

urlpatterns = [path("", views.send_feedback_view, name="send_feedback")]
