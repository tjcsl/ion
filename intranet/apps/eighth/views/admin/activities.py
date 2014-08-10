# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import cPickle
import logging
from django import http
from django.contrib import messages
from django.core.urlresolvers import reverse
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
        activity = EighthActivity.undeleted_objects.get(id=activity_id)
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

    context = {
        "form": form,
        "admin_page_title": "Edit Activity",
        "delete_url": reverse("eighth_admin_delete_activity",
                              args=[activity_id])
    }

    return render(request, "eighth/admin/edit_form.html", context)


@eighth_admin_required
def delete_activity_view(request, activity_id=None):
    try:
        activity = EighthActivity.objects.get(id=activity_id)
    except EighthActivity.DoesNotExist:
        return http.HttpResponseNotFound()

    if request.method == "POST":
        activity.deleted = True
        activity.save()
        messages.success(request, "Successfully deleted activity.")
        return redirect("eighth_admin_dashboard")
    else:
        context = {
            "admin_page_title": "Delete Activity",
            "help_text": "Deleting will not destroy past attendance data for this "
                         "activity. The activity will just be marked as deleted "
                         "and hidden from non-attendance views."
        }

        return render(request, "eighth/admin/delete_form.html", context)
