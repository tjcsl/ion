# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from django.http import Http404
from django.shortcuts import redirect, render
from ...auth.decorators import eighth_admin_required
from ...users.models import User

logger = logging.getLogger(__name__)

@eighth_admin_required
def profile_view(request, user_id=None):
    if user_id:
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise Http404
    else:
        user = request.user

    context = {
        "profile_user": user
    }
    return render(request, "eighth/profile.html", context)
