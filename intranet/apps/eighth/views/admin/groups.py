# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import cPickle
import csv
from django import http
from django.contrib import messages
from django.contrib.auth.models import Group
from django.shortcuts import redirect, render
from ....auth.decorators import eighth_admin_required
from ...forms.admin.groups import QuickGroupForm, GroupForm


@eighth_admin_required
def add_group_view(request):
    if request.method == "POST":
        form = QuickGroupForm(request.POST)
        if form.is_valid():
            group = form.save()
            messages.success(request, "Successfully added group.")
            return redirect("eighth_admin_edit_group",
                            group_id=group.id)
        else:
            messages.error(request, "Error adding group.")
            request.session["add_group_form"] = cPickle.dumps(form)
            return redirect("eighth_admin_dashboard")
    else:
        return http.HttpResponseNotAllowed(["POST"], "405: METHOD NOT ALLOWED")


@eighth_admin_required
def edit_group_view(request, group_id):
    try:
        group = Group.objects.get(id=group_id)
    except Group.DoesNotExist:
        raise http.Http404

    if request.method == "POST":
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully edited group.")
            return redirect("eighth_admin_dashboard")
        else:
            messages.error(request, "Error adding group.")
    else:
        form = GroupForm(instance=group)

    context = {
        "form": form,
        "admin_page_title": "Edit Group"
    }
    return render(request, "eighth/admin/edit_form.html", context)


@eighth_admin_required
def download_group_csv_view(request, group_id):
    try:
        group = Group.objects.get(id=group_id)
    except Group.DoesNotExist:
        raise http.Http404

    response = http.HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=\"{}\"".format(group.name)

    writer = csv.writer(response)
    writer.writerow(["Last Name", "First Name", "Student ID", "Grade", "Email"])

    for user in group.user_set.all():
        row = []
        row.append(user.last_name)
        row.append(user.first_name)
        row.append(user.student_id)
        row.append(user.grade.number())
        emails = user.emails
        row.append(user.emails[0] if emails is not None and len(emails) else None)
        writer.writerow(row)

    return response
