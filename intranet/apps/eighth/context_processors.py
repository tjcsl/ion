# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .utils import get_start_date
from .models import EighthSignup


def start_date(request):
    """Add the start date to the context for eighth admin views."""

    if request.user.is_authenticated() and request.user.is_eighth_admin:
        return {
            "admin_start_date": get_start_date(request)
        }

    return {}


def absence_count(request):
    """Add the absence count to the context for students."""

    if request.user.is_authenticated() and request.user.is_student:
        count = (EighthSignup.objects
                             .filter(user=request.user,
                                     was_absent=True)
                             .count())

        notif = request.session.get('eighth_absence_notif_seen', False)
        if not notif:
            request.session['eighth_absence_notif_seen'] = True

        return {
            "eighth_absence_count": count,
            "eighth_absence_notif": not notif
        }

    return {}