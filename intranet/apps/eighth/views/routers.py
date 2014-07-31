"""
Views that render different pages depending on the user that
requests them.
"""

from django.core.urlresolvers import reverse, resolve
from django.contrib.auth.decorators import login_required


@login_required
def eighth_redirect_view(request):
    if request.user.is_student:
        view = "eighth_signup"
    elif request.user.is_eighth_admin:
        view = "eighth_admin_index"
    elif request.user.is_teacher or request.user.is_attendance_user:
        view = "eighth_attendance"
    else:
        view = "index"  # should never happen

    return resolve(reverse(view)).func(request)
