from django.urls import re_path

from . import views

urlpatterns = [re_path(r"^$", views.send_feedback_view, name="send_feedback")]
