# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from six.moves import cPickle as pickle
import csv
import logging
from django import http
from django.contrib import messages
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render, render_to_response
from formtools.wizard.views import SessionWizardView
from ....auth.decorators import eighth_admin_required
from ....users.models import User
from ...forms.admin.activities import ActivitySelectionForm, ScheduledActivityMultiSelectForm
from ...forms.admin.blocks import BlockSelectionForm
from ...forms.admin.groups import QuickGroupForm, GroupForm
from ...models import EighthScheduledActivity, EighthSignup

logger = logging.getLogger(__name__)

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
            try:
                request.session["add_group_form"] = pickle.dumps(form)
            except TypeError:
                """ Prevent pickle errors """
                pass
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
        "admin_page_title": "Edit Group",
        "delete_url": reverse("eighth_admin_delete_group",
                              args=[group_id])
    }
    return render(request, "eighth/admin/edit_form.html", context)


@eighth_admin_required
def delete_group_view(request, group_id):
    try:
        group = Group.objects.get(id=group_id)
    except Group.DoesNotExist:
        raise http.Http404

    if request.method == "POST":
        group.delete()
        messages.success(request, "Successfully deleted group.")
        return redirect("eighth_admin_dashboard")
    else:
        context = {
            "admin_page_title": "Delete Group",
            "item_name": str(group),
            "help_text": "Deleting this group will remove all records "
                         "of it related to eighth period."
        }

        return render(request, "eighth/admin/delete_form.html", context)


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
        row.append(user.grade.number)
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
            "block": "Select a block",
            "activity": "Select an activity",
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
        scheduled_activity = EighthScheduledActivity.objects.get(
            block=block,
            activity=activity
        )

        try:
            group = Group.objects.get(id=kwargs["group_id"])
        except Group.DoesNotExist:
            raise http.Http404

        users = group.user_set.all()

        if not activity.both_blocks:
            EighthSignup.objects.filter(
                user__in=users,
                scheduled_activity__block=block
            ).delete()
            for user in users:
                EighthSignup.objects.create(
                    user=user,
                    scheduled_activity=scheduled_activity
                )
        else:
            EighthSignup.objects.filter(
                user__in=users,
                scheduled_activity__block__date=block.date
            )
            for user in users:
                all_sched_acts = EighthScheduledActivity.objects.filter(
                    block__date=block.date,
                    activity=activity
                )
                for sched_act in all_sched_acts:
                    EighthSignup.objects.create(
                        user=user,
                        scheduled_activity=sched_act
                    )

        messages.success(self.request, "Successfully signed up group for activity.")
        return redirect("eighth_admin_dashboard")

eighth_admin_signup_group = eighth_admin_required(
    EighthAdminSignUpGroupWizard.as_view(
        EighthAdminSignUpGroupWizard.FORMS
    )
)

class EighthAdminDistributeGroupWizard(SessionWizardView):
    FORMS = [
        ("block", BlockSelectionForm),
        ("activity", ScheduledActivityMultiSelectForm),
    ]

    TEMPLATES = {
        "block": "eighth/admin/distribute_group.html",
        "activity": "eighth/admin/distribute_group.html",
        "choose": "eighth/admin/distribute_group.html",
    }

    def get_template_names(self):
        return [self.TEMPLATES[self.steps.current]]

    def get_form_kwargs(self, step):
        kwargs = {}
        if step == "activity":
            block = self.get_cleaned_data_for_step("block")["block"]
            kwargs.update({"block": block})

        labels = {
            "block": "Select a block",
            "activity": "Select multiple activities",
        }

        kwargs.update({"label": labels[step]})

        return kwargs

    def get_context_data(self, form, **kwargs):
        context = super(EighthAdminDistributeGroupWizard,
                        self).get_context_data(form=form, **kwargs)
        context.update({"admin_page_title": "Distribute Group"})
        return context

    def done(self, form_list, **kwargs):
        block = form_list[0].cleaned_data["block"]
        activities = form_list[1].cleaned_data["activities"]
        
        logger.debug(block)
        logger.debug(activities)



        args = "block={}".format(block.id)
        for a in activities:
            args += "&activity={}".format(a.id)

        if "group_id" in kwargs:
            gid = kwargs["group_id"]
            args += "&group={}".format(gid)
        else:
            args += "&unsigned=1"

        return redirect("/eighth/admin/groups/distribute_action?{}".format(args))

eighth_admin_distribute_group = eighth_admin_required(
    EighthAdminDistributeGroupWizard.as_view(
        EighthAdminDistributeGroupWizard.FORMS
    )
)

@eighth_admin_required
def eighth_admin_distribute_action(request):
    if "users" in request.POST:
        logger.debug(request.POST)
        activity_user_map = {}
        for item in request.POST:
            if item[:6] == "schact":
                try:
                    sid = int(item[6:])
                    schact = EighthScheduledActivity.objects.get(id=sid)
                except EighthScheduledActivity.DoesNotExist:
                    messages.error(request, "ScheduledActivity does not exist with id {}".format(sid))

                userids = request.POST.getlist(item)
                activity_user_map[schact] = userids

        changes = 0
        logger.debug(activity_user_map)
        for schact, userids in activity_user_map.items():
            EighthSignup.objects.filter(
                user__id__in=userids,
                scheduled_activity__block=schact.block
            ).delete()
            for uid in userids:
                changes += 1
                EighthSignup.objects.create(
                    user=User.objects.get(id=int(uid)),
                    scheduled_activity=schact
                )

        messages.success(request, "Successfully signed up users for {} activities.".format(changes))

        return redirect("eighth_admin_dashboard")
    elif "activity" in request.GET and "block" in request.GET:
        blockid = request.GET.get("block")
        activityids = request.GET.getlist("activity")

        schacts = []
        for act in activityids:
            try:
                sch = EighthScheduledActivity.objects.get(block__id=blockid,
                                                          activity__id=act)
                schacts.append(sch)
            except EighthScheduledActivity.DoesNotExist:
                messages.error(request, "An eighth scheduled activity for {} on {} did not exist.".format(act, block))

        users = []
        if "group" in request.GET:
            group = Group.objects.get(id=request.GET.get("group"))
            users = group.user_set.all()
        elif "unsigned" in request.GET:
            unsigned = []

            students = User.objects.filter(username__startswith="2")
            for student in students:
                try:
                    su = EighthSignup.objects.get(user=student, scheduled_activity__block__id=blockid)
                except EighthSignup.DoesNotExist:
                    unsigned.append(student)

            users = unsigned



        context = {
            "schacts": schacts,
            "users": users,
            "show_selection": True
        }

        return render(request, "eighth/admin/distribute_group.html", context)
    else:
        return redirect("eighth_admin_dashboard")
            





