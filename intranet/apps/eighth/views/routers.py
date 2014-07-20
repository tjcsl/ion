"""
Views that render differently depending on the user that requests them.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


@login_required
def eighth_redirect_view(request):
    if request.user.is_eighth_admin:
        view = "eighth_admin"
    elif request.user.is_teacher or request.user.is_attendance_user:
        view = "eighth_attendance"
    elif request.user.is_student:
        view = "eighth_signup"
    else:
        view = "index"  # should never happen

    return redirect(view)
