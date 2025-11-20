from django.urls import path

from . import views

urlpatterns = [
    path("/student", views.student_welcome_view, name="welcome_student"),
    path("/teacher", views.teacher_welcome_view, name="welcome_teacher"),
    path("/done", views.done_welcome_view, name="welcome_done"),
    path("", views.welcome_view, name="welcome"),
]
