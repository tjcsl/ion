# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from six.moves import cPickle as pickle
import logging
from django import http, forms
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render
from ....auth.decorators import eighth_admin_required
from ....groups.models import Group
from ...forms.admin.activities import QuickActivityForm, ActivityForm
from ...models import EighthActivity

logger = logging.getLogger(__name__)


@eighth_admin_required
def add_activity_view(request):
    if request.method == "POST":
        form = QuickActivityForm(request.POST)
        if form.is_valid():
            activity = form.save()
            messages.success(request, "Successfully added activity.")
            return redirect("eighth_admin_edit_activity",
                            activity_id=activity.id)
        else:
            messages.error(request, "Error adding activity.")
            request.session["add_activity_form"] = pickle.dumps(form)
            return redirect("eighth_admin_dashboard")
    else:
        return http.HttpResponseNotAllowed(["POST"], "HTTP 405: METHOD NOT ALLOWED")


@eighth_admin_required
def edit_activity_view(request, activity_id):
    try:
        activity = EighthActivity.undeleted_objects.get(id=activity_id)
    except EighthActivity.DoesNotExist:
        raise http.Http404

    if request.method == "POST":
        form = ActivityForm(request.POST, instance=activity)
        if form.is_valid():
            try:
                form.save()
            except forms.ValidationError as error:
                error = str(error)
                messages.error(request, error)
            else:
                messages.success(request, "Successfully edited activity.")
                if "add_group" in request.POST:
                    grp_name = "Activity: {}".format(activity.name)
                    grp, status = Group.objects.get_or_create(name=grp_name)
                    logger.debug(grp)
                    activity.restricted = True
                    activity.groups_allowed.add(grp)
                    activity.save()
                    messages.success(request, "{} to '{}' group".format("Created and added" if status else "Added", grp_name))
                    return redirect("eighth_admin_edit_group", grp.id)

                return redirect("eighth_admin_edit_activity", activity_id)
        else:
            messages.error(request, "Error adding activity.")
    else:
        form = ActivityForm(instance=activity)

    activities = EighthActivity.undeleted_objects.order_by("name")
    context = {
        "form": form,
        "admin_page_title": "Edit Activity",
        "delete_url": reverse("eighth_admin_delete_activity",
                              args=[activity_id]),
        "activity": activity,
        "activities": activities
    }

    return render(request, "eighth/admin/edit_activity.html", context)


@eighth_admin_required
def delete_activity_view(request, activity_id=None):
    try:
        activity = EighthActivity.objects.get(id=activity_id)
    except EighthActivity.DoesNotExist:
        raise http.Http404

    perm_delete = False
    if activity.deleted and "perm" in request.GET:
        perm_delete = True

    if request.method == "POST":
        if perm_delete:
            activity.delete()
        else:
            activity.deleted = True
            activity.save()
        messages.success(request, "Successfully deleted activity.")
        return redirect("eighth_admin_dashboard")
    else:
        context = {
            "admin_page_title": "Delete Activity",
            "item_name": activity.name,
            "help_text": ("Deleting will not destroy past attendance data for this "
                          "activity. The activity will just be marked as deleted "
                          "and hidden from non-attendance views." if not perm_delete
                          else "This will destroy past attendance data.")
        }

        return render(request, "eighth/admin/delete_form.html", context)
