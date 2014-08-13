# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import cPickle
import csv
from django import http
from django.contrib import messages
from django.contrib.auth.models import Group
from django.contrib.formtools.wizard.views import SessionWizardView
from django.shortcuts import redirect, render
from ....auth.decorators import eighth_admin_required
from ...forms.admin.activities import ActivitySelectionForm
from ...forms.admin.blocks import BlockSelectionForm
from ...forms.admin.groups import QuickGroupForm, GroupForm
from ...models import EighthScheduledActivity, EighthSignup


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


class EighthAdminSignUpGroupWizard(SessionWizardView):
    FORMS = [
        ("block", BlockSelectionForm),
        ("activity", ActivitySelectionForm),
    ]

    TEMPLATES = {
        "block": "eighth/admin/sign_up_group.html",
        "activity": "eighth/admin/sign_up_group.html",
    }

    def get_template_names(self):
        return [self.TEMPLATES[self.steps.current]]

    def get_form_kwargs(self, step):
        kwargs = {}
        if step == "activity":
            block = self.get_cleaned_data_for_step("block")["block"]
            kwargs.update({"block": block})

        labels = {
            "block": "Select a block for which to sign up group",
            "activity": "Select an activity for which to sign up group",
        }

        kwargs.update({"label": labels[step]})

        return kwargs

    def get_context_data(self, form, **kwargs):
        context = super(EighthAdminSignUpGroupWizard,
                        self).get_context_data(form=form, **kwargs)
        context.update({"admin_page_title": "Sign Up Group"})
        return context

    def done(self, form_list, **kwargs):
        block = form_list[0].cleaned_data["block"]
        activity = form_list[1].cleaned_data["activity"]
        scheduled_activity = EighthScheduledActivity.objects \
                                                    .get(block=block,
                                                         activity=activity)

        try:
            group = Group.objects.get(id=kwargs["group_id"])
        except Group.DoesNotExist:
            raise http.Http404

        users = group.user_set.all()

        if not activity.both_blocks:
            EighthSignup.objects \
                        .filter(user__in=users,
                                scheduled_activity__block=block) \
                        .delete()
            for user in users:
                EighthSignup.objects \
                            .create(user=user,
                                    scheduled_activity=scheduled_activity)
        else:
            EighthSignup.objects \
                        .filter(user__in=users,
                                scheduled_activity__block__date=block.date)
            for user in users:
                all_sched_acts = EighthScheduledActivity.objects \
                                                        .filter(block__date=block.date,
                                                                activity=activity)
                for sched_act in all_sched_acts:
                    EighthSignup.objects \
                                .create(user=user,
                                        scheduled_activity=sched_act)

        messages.success(self.request, "Successfully signed up group for activity.")
        return redirect("eighth_admin_dashboard")
