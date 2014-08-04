# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import cPickle
import logging
from django import http
from django.contrib import messages
from django.shortcuts import redirect, render
from ....auth.decorators import eighth_admin_required
from ...forms.admin.activities import QuickActivityForm, ActivityForm
from ...models import EighthActivity

logger = logging.getLogger(__name__)


@eighth_admin_required
def add_activity_view(request):
    if request.method == "POST":
        form = QuickActivityForm(request.POST)
        logger.error("{}".format(request.POST["name"]))
        if form.is_valid():
            activity = form.save()
            messages.success(request, "Successfully added activity.")
            return redirect("eighth_admin_edit_activity",
                            activity_id=activity.id)
        else:
            messages.error(request, "Error adding activity.")
            request.session["add_activity_form"] = cPickle.dumps(form)
            return redirect("eighth_admin_dashboard")
    else:
        return http.HttpResponseNotAllowed(["POST"], "HTTP 405: METHOD NOT ALLOWED")


@eighth_admin_required
def edit_activity_view(request, activity_id=None):
    try:
        activity = EighthActivity.objects.get(id=activity_id)
    except EighthActivity.DoesNotExist:
        return http.HttpResponseNotFound()

    if request.method == "POST":
        form = ActivityForm(request.POST, instance=activity)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully edited activity.")
            return redirect("eighth_admin_dashboard")
        else:
            messages.error(request, "Error adding activity.")
    else:
        form = ActivityForm(instance=activity)

    return render(request, "eighth/admin/edit_activity.html", {"form": form})
