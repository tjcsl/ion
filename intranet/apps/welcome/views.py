# -*- coding: utf-8 -*-

import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

logger = logging.getLogger(__name__)


@login_required
def student_welcome_view(request):
    """Welcome/first run page for students."""
    if not request.user.is_student:
        return redirect("index")
    context = {"first_login": request.session["first_login"] if "first_login" in request.session else False}
    return render(request, "welcome/student.html", context)


@login_required
def teacher_welcome_view(request):
    # if not request.is_teacher:
    #   return redirect("index")
    context = {"first_login": request.session["first_login"] if "first_login" in request.session else False}
    return render(request, "welcome/teacher.html", context)


@login_required
def done_welcome_view(request):
    request.user.seen_welcome = True
    request.user.save()
    return redirect("index")


@login_required
def welcome_view(request):
    if request.user.is_teacher:
        return teacher_welcome_view(request)
    elif request.user.is_student:
        return student_welcome_view(request)
    else:
        return redirect("index")
