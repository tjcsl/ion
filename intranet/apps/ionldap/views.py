# -*- coding: utf-8 -*-

import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

logger = logging.getLogger(__name__)


@login_required
def main_view(request):
    """Show the current user's class schedule."""

    user = request.user
    courses = user.ldapcourse_set.all().order_by("period", "end_period")

    context = {
        "user": user,
        "courses": courses
    }
    return render(request, "ionldap/main.html", context)
