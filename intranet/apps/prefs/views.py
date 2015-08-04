# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

logger = logging.getLogger(__name__)


@login_required
def prefs_view(request):
    """The main prefs view."""
    return render(request, "prefs/prefs.html")
