""" Main views """
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from intranet.apps.auth.decorators import eighth_admin_required, eighth_teacher_required
import logging
logger = logging.getLogger(__name__)

@login_required
def eighth_redirect_view(request):
    if request.user.is_eighth_admin:
        pg = "admin"
    elif request.user.is_teacher:
        pg = "teacher"
    elif request.user.is_student:
        pg = "signup"
    else:
        pg = ".."
    return redirect("/eighth/" + pg)

@eighth_admin_required
def eighth_admin_view(request):
    return render(request, "eighth/admin.html", {
        "page": "eighth_admin",
        "success": 'success' in request.POST
    })


@eighth_teacher_required
def eighth_teacher_view(request):
    return render(request, "eighth/teacher.html", {"page": "eighth_teacher"})

