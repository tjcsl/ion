import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from ..dashboard.views import dashboard_view

logger = logging.getLogger(__name__)


@login_required
def student_welcome_view(request):
    """Welcome/first run page for students."""
    return dashboard_view(request, show_welcome=True)


@login_required
def teacher_welcome_view(request):
    context = {"first_login": request.session["first_login"] if "first_login" in request.session else False}
    return render(request, "welcome/teacher.html", context)


@login_required
def welcome_view(request):
    if request.user.is_teacher:
        return teacher_welcome_view(request)
    elif request.user.is_student:
        return student_welcome_view(request)
    else:
        return redirect("index")
