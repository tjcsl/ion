# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .utils import get_start_date


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
        absence_info = request.user.absence_info()
        num_absences = absence_info.count()
        show_notif = False
        if num_absences > 0:
            notif_seen = request.session.get('eighth_absence_notif_seen', False)
            if not notif_seen:
                for signup in absence_info:
                    if signup.in_clear_absence_period():
                        show_notif = True

            if show_notif:
                request.session['eighth_absence_notif_seen'] = True
            

        return {
            "eighth_absence_count": num_absences,
            "eighth_absence_notif": show_notif
        }

    return {}
