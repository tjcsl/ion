import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from ..auth.decorators import deny_restricted
from ..dashboard.views import dashboard_view

logger = logging.getLogger(__name__)


@login_required
@deny_restricted
def student_welcome_view(request):
    """Welcome/first run page for students."""
    return dashboard_view(request, show_welcome=True)


@login_required
@deny_restricted
def teacher_welcome_view(request):
    context = {"first_login": request.session["first_login"] if "first_login" in request.session else False}
    return render(request, "welcome/teacher.html", context)


@login_required
@deny_restricted
def welcome_view(request):
    if request.user.is_teacher:
        return teacher_welcome_view(request)
    elif request.user.is_student:
        return student_welcome_view(request)
    else:
        return redirect("index")


@login_required
@deny_restricted
def done_welcome_view(request):
    request.user.seen_welcome = True
    request.user.save()
    return redirect("index")
