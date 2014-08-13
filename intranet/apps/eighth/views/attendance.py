# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
from django.contrib.formtools.wizard.views import SessionWizardView
from django.shortcuts import render, redirect
from ..utils import get_start_date
from ..forms.admin.activities import ActivitySelectionForm
from ..forms.admin.blocks import BlockSelectionForm
from ..models import EighthScheduledActivity, EighthSponsor


class EighthAttendanceSelectScheduledActivityWizard(SessionWizardView):
    FORMS = [
        ("block", BlockSelectionForm),
        ("activity", ActivitySelectionForm),
    ]

    TEMPLATES = {
        "block": "eighth/admin/attendance_select_scheduled_activity.html",
        "activity": "eighth/admin/attendance_select_scheduled_activity.html",
    }

    def get_template_names(self):
        return [self.TEMPLATES[self.steps.current]]

    def get_form_kwargs(self, step):
        kwargs = {}
        if step == "block":
            if not self.request.user.is_eighth_admin:
                now = datetime.datetime.now().date().date()
                kwargs.update({"exclude_before_date": now})
            else:
                start_date = get_start_date(self.request)
                kwargs.update({"exclude_before_date": start_date})

        if step == "activity":
            block = self.get_cleaned_data_for_step("block")["block"]
            kwargs.update({"block": block})

            try:
                sponsor = self.request.user.eighthsponsor
            except EighthSponsor.DoesNotExist:
                sponsor = None

            if not (self.request.user.is_eighth_admin or (sponsor is None)):
                kwargs.update({"sponsor": sponsor})

        labels = {
            "block": "Select a block",
            "activity": "Select an activity",
        }

        kwargs.update({"label": labels[step]})

        return kwargs

    def get_context_data(self, form, **kwargs):
        context = super(EighthAttendanceSelectScheduledActivityWizard,
                        self).get_context_data(form=form, **kwargs)
        context.update({"admin_page_title": "Take Attendance"})
        return context

    def done(self, form_list, **kwargs):
        block = form_list[0].cleaned_data["block"]
        activity = form_list[1].cleaned_data["activity"]
        scheduled_activity = EighthScheduledActivity.objects \
                                                    .get(block=block,
                                                         activity=activity)

        if "admin" in self.request.path:
            url_name = "eighth_admin_take_attendance"
        else:
            url_name = "eighth_take_attendance"

        return redirect(url_name, scheduled_activity_id=scheduled_activity.id)


def take_attendance_view(request, scheduled_activity_id):
    pass
