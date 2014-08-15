# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .utils import get_start_date


def start_date(request):
    """Add the start date to the context for eighth admin views
    """

    if request.user.is_authenticated() and request.user.is_eighth_admin:
        return {
            "admin_start_date": get_start_date(request)
        }

    return {}
