from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^/student$", views.student_welcome_view, name="welcome_student"),
    re_path(r"^/teacher$", views.teacher_welcome_view, name="welcome_teacher"),
    re_path(r"^/done$", views.done_welcome_view, name="welcome_done"),
    re_path(r"^$", views.welcome_view, name="welcome"),
]
