# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import resolve, reverse


"""
Views that render different pages depending on the user that
requests them.
"""


@login_required
def eighth_redirect_view(request):
    if request.user.is_student:
        view = "eighth_signup"
    elif request.user.is_eighth_admin:
        view = "eighth_admin_dashboard"
    elif request.user.is_teacher or request.user.is_attendance_user:
        view = "eighth_attendance_choose_scheduled_activity"
    else:
        view = "index"  # should never happen

    return resolve(reverse(view)).func(request)
