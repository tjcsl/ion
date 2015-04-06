# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
from six import BytesIO
from django import http
from django.shortcuts import render, redirect
from formtools.wizard.views import SessionWizardView
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from ...auth.decorators import eighth_admin_required, attendance_taker_required
from ..utils import get_start_date
from ..forms.admin.activities import ActivitySelectionForm
from ..forms.admin.blocks import BlockSelectionForm
from ..models import EighthScheduledActivity, EighthSponsor, EighthSignup


def should_show_activity_list(wizard):
    if wizard.request.user.is_eighth_admin:
        return True

    cleaned_data = wizard.get_cleaned_data_for_step("block") or {}

    if cleaned_data:
        activities = wizard.get_form("activity").fields["activity"].queryset
        if activities.count() == 1:
            wizard.default_activity = activities[0]
            return False
        if activities.count() == 0:
            wizard.no_activities = True
            return False
    return True


class EighthAttendanceSelectScheduledActivityWizard(SessionWizardView):
    FORMS = [
        ("block", BlockSelectionForm),
        ("activity", ActivitySelectionForm),
    ]

    TEMPLATES = {
        "block": "eighth/take_attendance.html",
        "activity": "eighth/take_attendance.html",
    }

    def get_template_names(self):
        return [self.TEMPLATES[self.steps.current]]

    def get_form_kwargs(self, step):
        kwargs = {}
        if step == "block":
            if not self.request.user.is_eighth_admin:
                now = datetime.datetime.now().date()
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
        if hasattr(self, "no_activities"):
            response = redirect("eighth_attendance_choose_scheduled_activity")
            response["Location"] += "?na=1"
            return response

        if hasattr(self, "default_activity"):
            activity = self.default_activity
        else:
            activity = form_list[1].cleaned_data["activity"]

        block = form_list[0].cleaned_data["block"]
        scheduled_activity = EighthScheduledActivity.objects.get(
            block=block,
            activity=activity
        )

        if "admin" in self.request.path:
            url_name = "eighth_admin_take_attendance"
        else:
            url_name = "eighth_take_attendance"

        return redirect(url_name, scheduled_activity_id=scheduled_activity.id)

_unsafe_choose_scheduled_activity_view = (
    EighthAttendanceSelectScheduledActivityWizard.as_view(
        EighthAttendanceSelectScheduledActivityWizard.FORMS,
        condition_dict={"activity": should_show_activity_list}
    )
)
teacher_choose_scheduled_activity_view = (
    attendance_taker_required(_unsafe_choose_scheduled_activity_view)
)
admin_choose_scheduled_activity_view = (
    eighth_admin_required(_unsafe_choose_scheduled_activity_view)
)


@attendance_taker_required
def take_attendance_view(request, scheduled_activity_id):
    try:
        scheduled_activity = (EighthScheduledActivity.objects
                                                     .select_related("activity",
                                                                     "block")
                                                     .get(cancelled=False,
                                                          activity__deleted=False,
                                                          id=scheduled_activity_id))
    except EighthScheduledActivity.DoesNotExist:
        raise http.Http404

    if request.method == "POST":
        present_user_ids = list(request.POST.keys())
        absent_signups = (EighthSignup.objects.filter(scheduled_activity=scheduled_activity)
                                      .exclude(user__in=present_user_ids))
        absent_signups.update(was_absent=True)

        present_signups = (EighthSignup.objects
                                       .filter(scheduled_activity=scheduled_activity,
                                               user__in=present_user_ids))
        present_signups.update(was_absent=False)

        passes = (EighthSignup.objects
                              .filter(scheduled_activity=scheduled_activity,
                                      after_deadline=True,
                                      pass_accepted=False)
                              .update(was_absent=True))

        scheduled_activity.attendance_taken = True
        scheduled_activity.save()

        if "admin" in request.path:
            url_name = "eighth_admin_take_attendance"
        else:
            url_name = "eighth_take_attendance"

        return redirect(url_name, scheduled_activity_id=scheduled_activity.id)
    else:
        passes = (EighthSignup.objects
                              .select_related("user")
                              .filter(scheduled_activity=scheduled_activity,
                                      after_deadline=True,
                                      pass_accepted=False))

        users = scheduled_activity.members.exclude(eighthsignup__in=passes)
        members = []

        absent_user_ids = (EighthSignup.objects
                                       .select_related("user")
                                       .filter(scheduled_activity=scheduled_activity,
                                               was_absent=True)
                                       .values_list("user__id", flat=True))

        for user in users:
            members.append({
                "id": user.id,
                "name": user.last_name + ", " + user.first_name,
                "grade": user.grade.number,
                "present": (scheduled_activity.attendance_taken and
                            (user.id not in absent_user_ids))
            })

        members.sort(key=lambda m: m["name"])

        context = {
            "scheduled_activity": scheduled_activity,
            "passes": passes,
            "members": members
        }

        return render(request, "eighth/take_attendance.html", context)


@attendance_taker_required
def accept_pass_view(request, signup_id):
    if request.method != "POST":
        return http.HttpResponseNotAllowed(["POST"])

    try:
        signup = EighthSignup.objects.get(id=signup_id)
    except EighthSignup.DoesNotExist:
        raise http.Http404

    signup.was_absent = False
    signup.pass_accepted = True
    signup.save()

    if "admin" in request.path:
        url_name = "eighth_admin_take_attendance"
    else:
        url_name = "eighth_take_attendance"

    return redirect(url_name,
                    scheduled_activity_id=signup.scheduled_activity.id)


@attendance_taker_required
def accept_all_passes_view(request, scheduled_activity_id):
    if request.method != "POST":
        return http.HttpResponseNotAllowed(["POST"])

    try:
        scheduled_activity = EighthScheduledActivity.objects.get(
            id=scheduled_activity_id
        )
    except EighthScheduledActivity.DoesNotExist:
        raise http.Http404

    EighthSignup.objects.filter(
        after_deadline=True,
        scheduled_activity=scheduled_activity
    ).update(
        pass_accepted=True,
        was_absent=False
    )

    if "admin" in request.path:
        url_name = "eighth_admin_take_attendance"
    else:
        url_name = "eighth_take_attendance"

    return redirect(url_name,
                    scheduled_activity_id=scheduled_activity.id)


def generate_roster_pdf(sched_act_ids, include_instructions):
    """Generates a PDF roster for one or more
    :class:`EighthScheduledActivity`\s.

    Args
        sched_act_ids
            The list of IDs of the scheduled activities to show in the PDF.
        include_instructions
            Whether instructions should be printed at the bottom of the
            roster(s).

    Returns a BytesIO object for the PDF.

    """

    pdf_buffer = BytesIO()
    h_margin = 1 * inch
    v_margin = 0.5 * inch
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter,
                            rightMargin=h_margin, leftMargin=h_margin,
                            topMargin=v_margin, bottomMargin=v_margin)

    elements = []

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Center", alignment=TA_CENTER))
    styles.add(ParagraphStyle(name="BlockLetter", fontSize=60, leading=72, alignment=TA_CENTER))
    styles.add(ParagraphStyle(name="ActivityAttribute", fontSize=15, leading=18, alignment=TA_RIGHT))

    for i, said in enumerate(sched_act_ids):
        sact = EighthScheduledActivity.objects.get(id=said)

        sponsor_names = sact.get_true_sponsors().values_list("first_name",
                                                             "last_name")
        sponsors_str = "; ".join(l + ", " + f for f, l in sponsor_names)

        room_names = sact.get_true_rooms().values_list("name", flat=True)
        rooms_str = ", ".join("Room " + r for r in room_names)

        header_data = [[
            Paragraph("<b>Activity ID {}</b>".format(sact.activity.id), styles["Normal"]),
            Paragraph("{}<br/>{}<br/>{}".format(sponsors_str,
                                                rooms_str,
                                                sact.block.date),
                      styles["ActivityAttribute"]),
            Paragraph("A", styles["BlockLetter"])
        ]]
        header_style = TableStyle([
            ("VALIGN", (0, 0), (0, 0), "TOP"),
            ("VALIGN", (1, 0), (2, 0), "MIDDLE"),
            ("TOPPADDING", (0, 0), (0, 0), 15),
            ("RIGHTPADDING", (1, 0), (1, 0), 0),
        ])

        elements.append(Table(header_data, style=header_style, colWidths=[2 * inch, None, 1 * inch]))
        elements.append(Spacer(0, 10))
        elements.append(Paragraph(sact.activity.name, styles["Title"]))
        elements.append(Paragraph("{} Students".format(sact.members.count()), styles["Center"]))
        elements.append(Spacer(0, 5))

        attendance_data = [[Paragraph("Present", styles["Heading5"]), Paragraph("Student Name (ID)", styles["Heading5"]), Paragraph("Grade", styles["Heading5"])]]

        members = []
        for member in sact.members.all():
            members.append((member.last_name + ", " + member.first_name, member.id))
        members = sorted(members)

        for member_name, member_id in members:
            row = ["_____________", "{} ({})".format(member_name, member_id), "12"]
            attendance_data.append(row)

        # Line commands are like this:
        # op, start, stop, weight, colour, cap, dashes, join, linecount, linespacing
        # For some reason, LINEBELOW doesn't work right, so the Present line is achieved
        # with underscores... Not great but it works.
        attendance_style = TableStyle([
            ("LINEABOVE", (0, 1), (2, 1), 1, colors.black, None, None, None, 2, None),
            # ("LINEBELOW", (0, 2), (0, len(attendance_data)), 1, colors.black, None, None, None, None, None),
            ("TOPPADDING", (0, 1), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
        ])

        elements.append(Table(attendance_data, style=attendance_style, colWidths=[1.3 * inch, None, 0.8 * inch]))
        elements.append(Spacer(0, 15))
        instructions = """Underline, highlight, or circle the names and ID numbers of the students who are <b>no-shows</b>.<br/>
        Return the <b>roster</b> and <b>passes</b> to Eighth Period coordinator Joan Burch's mailbox
        in the <b>main office</b>.<br/>
        <b>Do not make any additions to the roster.</b><br/>
        Students who need changes should report to the 8th period office.<br/>
        For questions, please call extension 5046 or 5078. Thank you!<br/>"""
        elements.append(Paragraph(instructions, styles["Normal"]))

        if i != len(sched_act_ids) - 1:
            elements.append(PageBreak())

    doc.build(elements)
    return pdf_buffer
