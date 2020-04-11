import csv
import logging
from html import escape
from io import BytesIO

from cacheops import invalidate_obj
from formtools.wizard.views import SessionWizardView
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from django import http
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from ....utils.date import get_date_range_this_year
from ...auth.decorators import attendance_taker_required, deny_restricted, eighth_admin_required
from ...dashboard.views import gen_sponsor_schedule
from ...schedule.views import decode_date
from ..forms.admin.activities import ActivitySelectionForm
from ..forms.admin.blocks import BlockSelectionForm
from ..models import EighthActivity, EighthBlock, EighthScheduledActivity, EighthSignup, EighthSponsor, EighthWaitlist
from ..tasks import email_scheduled_activity_students_task
from ..utils import get_start_date

logger = logging.getLogger(__name__)


def should_show_activity_list(wizard):
    if "default_activity" in wizard.request.GET:
        act_id = wizard.request.GET["default_activity"]
        default_activity = EighthActivity.objects.filter(id=act_id)

        if default_activity.count() == 1:
            wizard.default_activity = default_activity[0]
            return False

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
    FORMS = [("block", BlockSelectionForm), ("activity", ActivitySelectionForm)]

    TEMPLATES = {"block": "eighth/take_attendance.html", "activity": "eighth/take_attendance.html"}

    def get_template_names(self):
        return [self.TEMPLATES[self.steps.current]]

    def get_form_kwargs(self, step=None):
        kwargs = {}
        block = None

        if step == "block":
            show_all_blocks = "show_all_blocks" in self.request.GET or "block" in self.request.GET
            if show_all_blocks:
                """Only show blocks after September 1st of the current school year."""
                now, _ = get_date_range_this_year()
                kwargs.update({"exclude_before_date": now})
            elif not self.request.user.is_eighth_admin:
                now = timezone.localdate()
                kwargs.update({"exclude_before_date": now})
            else:
                start_date = get_start_date(self.request)
                kwargs.update({"exclude_before_date": start_date})

        if step == "activity":
            block = self.get_cleaned_data_for_step("block")
            if block:
                block = block["block"]
                kwargs.update({"block": block})
                if self.request and self.request.user and self.request.user.is_eighthoffice:
                    kwargs.update({"include_cancelled": True})
                block_title = "Take Attendance" if block.locked else "View Roster"

            try:
                sponsor = self.request.user.eighthsponsor
            except (EighthSponsor.DoesNotExist, AttributeError):
                sponsor = None

            if self.request.user.is_restricted and sponsor is not None:
                kwargs.update({"sponsor": sponsor})

        labels = {"block": "Select a block", "activity": "Select an activity" if not block else block_title}

        kwargs.update({"label": labels[step]})

        return kwargs

    def get_context_data(self, form, **kwargs):
        context = super(EighthAttendanceSelectScheduledActivityWizard, self).get_context_data(form=form, **kwargs)
        context.update({"admin_page_title": "Take Attendance"})

        block = self.get_cleaned_data_for_step("block")
        context.update({"show_all_blocks": ("show_all_blocks" in self.request.GET or "block" in self.request.GET)})
        context.update({"default_activity_not_scheduled": ("default_activity" in self.request.GET and not block)})

        if block:
            block = block["block"]
            try:
                sponsor = self.request.user.eighthsponsor
            except (EighthSponsor.DoesNotExist, AttributeError):
                sponsor = None

            if sponsor and not self.request.user.is_eighthoffice:
                context.update({"sponsor_block": block})

                sponsoring_filter = Q(sponsors=sponsor) | (Q(sponsors=None) & Q(activity__sponsors=sponsor))
                sponsored_activities = EighthScheduledActivity.objects.filter(block=block).filter(sponsoring_filter).order_by("activity__name")

                context.update({"sponsored_activities": sponsored_activities})
        elif "block" in self.request.GET:
            block_id = self.request.GET["block"]
            context["redirect_block_id"] = block_id

        return context

    def done(self, form_list, **kwargs):  # pylint: disable=unused-argument
        form_list = list(form_list)

        if hasattr(self, "no_activities"):
            response = redirect("eighth_attendance_choose_scheduled_activity")
            response["Location"] += "?na=1"
            return response

        if hasattr(self, "default_activity"):
            activity = self.default_activity  # pylint: disable=no-member; We just checked if the attribute exists
        else:
            activity = form_list[1].cleaned_data["activity"]

        block = form_list[0].cleaned_data["block"]
        try:
            scheduled_activity = EighthScheduledActivity.objects.get(block=block, activity=activity)
        except EighthScheduledActivity.DoesNotExist:
            raise http.Http404("The scheduled activity with block {} and activity {} does not exist.".format(block, activity))

        if "admin" in self.request.path:
            url_name = "eighth_admin_take_attendance"
        else:
            url_name = "eighth_take_attendance"

        return redirect(url_name, scheduled_activity_id=scheduled_activity.id)


_unsafe_choose_scheduled_activity_view = EighthAttendanceSelectScheduledActivityWizard.as_view(
    EighthAttendanceSelectScheduledActivityWizard.FORMS, condition_dict={"activity": should_show_activity_list}
)
teacher_choose_scheduled_activity_view = attendance_taker_required(_unsafe_choose_scheduled_activity_view)
admin_choose_scheduled_activity_view = eighth_admin_required(_unsafe_choose_scheduled_activity_view)


@login_required
@deny_restricted
def roster_view(request, scheduled_activity_id):
    try:
        scheduled_activity = EighthScheduledActivity.objects.get(id=scheduled_activity_id)
    except EighthScheduledActivity.DoesNotExist:
        raise http.Http404

    signups = EighthSignup.objects.filter(scheduled_activity=scheduled_activity)

    viewable_members = scheduled_activity.get_viewable_members(request.user)
    num_hidden_members = len(scheduled_activity.get_hidden_members(request.user))
    is_sponsor = scheduled_activity.user_is_sponsor(request.user)
    context = {
        "scheduled_activity": scheduled_activity,
        "viewable_members": viewable_members,
        "num_hidden_members": num_hidden_members,
        "signups": signups,
        "is_sponsor": is_sponsor,
    }

    return render(request, "eighth/roster.html", context)


@login_required
def raw_roster_view(request, scheduled_activity_id):
    try:
        scheduled_activity = EighthScheduledActivity.objects.get(id=scheduled_activity_id)
    except EighthScheduledActivity.DoesNotExist:
        raise http.Http404

    signups = EighthSignup.objects.filter(scheduled_activity=scheduled_activity)

    viewable_members = scheduled_activity.get_viewable_members(request.user)
    num_hidden_members = scheduled_activity.get_hidden_members(request.user).count()

    context = {
        "scheduled_activity": scheduled_activity,
        "viewable_members": viewable_members,
        "num_hidden_members": num_hidden_members,
        "signups": signups,
    }

    return render(request, "eighth/roster_list.html", context)


@eighth_admin_required
@deny_restricted
def raw_waitlist_view(request, scheduled_activity_id):
    try:
        scheduled_activity = EighthScheduledActivity.objects.get(id=scheduled_activity_id)
    except EighthScheduledActivity.DoesNotExist:
        raise http.Http404

    context = {"ordered_waitlist": EighthWaitlist.objects.filter(scheduled_activity_id=scheduled_activity.id).order_by("time")}
    return render(request, "eighth/waitlist_list.html", context)


@attendance_taker_required
def take_attendance_view(request, scheduled_activity_id):
    try:
        scheduled_activity = EighthScheduledActivity.objects.select_related("activity", "block").get(
            activity__deleted=False, id=scheduled_activity_id
        )
    except EighthScheduledActivity.DoesNotExist:
        raise http.Http404

    # Attendance-only users can only see their own roster
    if request.user.is_restricted and not scheduled_activity.user_is_sponsor(request.user):
        raise http.Http404

    edit_perm = request.user.is_eighth_admin or scheduled_activity.user_is_sponsor(request.user)

    edit_perm_cancelled = False

    if scheduled_activity.cancelled and not request.user.is_eighth_admin:
        edit_perm = False
        edit_perm_cancelled = True

    if request.method == "POST":

        if not edit_perm:
            if edit_perm_cancelled:
                return render(
                    request,
                    "error/403.html",
                    {"reason": "You do not have permission to take attendance for this activity. The activity was cancelled."},
                    status=403,
                )
            else:
                return render(
                    request,
                    "error/403.html",
                    {"reason": "You do not have permission to take attendance for this activity. You are not a sponsor."},
                    status=403,
                )

        if "admin" in request.path:
            url_name = "eighth_admin_take_attendance"
        else:
            url_name = "eighth_take_attendance"

        if "clear_attendance_bit" in request.POST:
            scheduled_activity.attendance_taken = False
            scheduled_activity.save()
            invalidate_obj(scheduled_activity)

            messages.success(request, "Attendance bit cleared for {}".format(scheduled_activity))

            redirect_url = reverse(url_name, args=[scheduled_activity.id])

            if "no_attendance" in request.GET:
                redirect_url += "?no_attendance={}".format(request.GET["no_attendance"])

            return redirect(redirect_url)

        if not scheduled_activity.block.locked and not request.user.is_eighth_admin:
            return render(
                request,
                "error/403.html",
                {"reason": "You do not have permission to take attendance for this activity. The block has not been locked yet."},
                status=403,
            )

        if not scheduled_activity.block.locked and request.user.is_eighth_admin:
            messages.success(request, "Note: Taking attendance on an unlocked block.")

        present_user_ids = list(request.POST.keys())

        csrf = "csrfmiddlewaretoken"
        if csrf in present_user_ids:
            present_user_ids.remove(csrf)

        absent_signups = EighthSignup.objects.filter(scheduled_activity=scheduled_activity).exclude(user__in=present_user_ids)
        absent_signups.update(was_absent=True)

        for s in absent_signups:
            invalidate_obj(s)

        present_signups = EighthSignup.objects.filter(scheduled_activity=scheduled_activity, user__in=present_user_ids)
        present_signups.update(was_absent=False)

        for s in present_signups:
            invalidate_obj(s)

        passes = EighthSignup.objects.filter(scheduled_activity=scheduled_activity, after_deadline=True, pass_accepted=False)
        passes.update(was_absent=True)

        for s in passes:
            invalidate_obj(s)

        scheduled_activity.attendance_taken = True
        scheduled_activity.save()
        invalidate_obj(scheduled_activity)

        messages.success(request, "Attendance updated.")

        redirect_url = reverse(url_name, args=[scheduled_activity.id])

        if "no_attendance" in request.GET:
            redirect_url += "?no_attendance={}".format(request.GET["no_attendance"])

        return redirect(redirect_url)
    else:
        passes = EighthSignup.objects.select_related("user").filter(scheduled_activity=scheduled_activity, after_deadline=True, pass_accepted=False)

        users = scheduled_activity.members.exclude(eighthsignup__in=passes)
        members = []

        absent_user_ids = (
            EighthSignup.objects.select_related("user")
            .filter(scheduled_activity=scheduled_activity, was_absent=True)
            .values_list("user__id", flat=True)
        )

        pass_users = (
            EighthSignup.objects.select_related("user")
            .filter(scheduled_activity=scheduled_activity, after_deadline=True, pass_accepted=True)
            .values_list("user__id", flat=True)
        )

        for user in users:
            members.append(
                {
                    "id": user.id,
                    "name": user.last_first,  # includes nickname
                    "grade": user.grade.number if user.grade else None,
                    "present": (scheduled_activity.attendance_taken and (user.id not in absent_user_ids)),
                    "had_pass": user.id in pass_users,
                    "pass_present": (not scheduled_activity.attendance_taken and user.id in pass_users and user.id not in absent_user_ids),
                    "email": user.tj_email,
                }
            )
            invalidate_obj(user)

        members.sort(key=lambda m: m["name"])

        context = {
            "scheduled_activity": scheduled_activity,
            "passes": passes,
            "members": members,
            "p": pass_users,
            "no_edit_perm": not edit_perm,
            "edit_perm_cancelled": edit_perm_cancelled,
            "show_checkboxes": (scheduled_activity.block.locked or request.user.is_eighth_admin),
            "show_icons": (scheduled_activity.block.locked and scheduled_activity.block.attendance_locked() and not request.user.is_eighth_admin),
        }

        if request.user.is_eighth_admin:
            context["scheduled_activities"] = EighthScheduledActivity.objects.filter(block__id=scheduled_activity.block.id)
            context["blocks"] = EighthBlock.objects.filter(date__gte=get_start_date(request)).order_by("date", "block_letter")

        if request.resolver_match.url_name == "eighth_admin_export_attendance_csv":
            response = http.HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = 'attachment; filename="attendance.csv"'

            writer = csv.writer(response)
            writer.writerow(
                [
                    "Block",
                    "Activity",
                    "Name",
                    "Student ID",
                    "Grade",
                    "Email",
                    "Locked",
                    "Rooms",
                    "Sponsors",
                    "Attendance Taken",
                    "Present",
                    "Had Pass",
                ]
            )
            for member in members:
                row = []
                row.append(str(scheduled_activity.block))
                row.append(str(scheduled_activity.activity))
                row.append(member["name"])
                row.append(member["id"])
                row.append(member["grade"])
                row.append(member["email"])
                row.append(scheduled_activity.block.locked)
                rooms = scheduled_activity.get_true_rooms()
                row.append(", ".join(["{} ({})".format(room.name, room.capacity) for room in rooms]))
                sponsors = scheduled_activity.get_true_sponsors()
                row.append(" ,".join([sponsor.name for sponsor in sponsors]))
                row.append(scheduled_activity.attendance_taken)
                row.append(member["present"] if scheduled_activity.block.locked else "N/A")

                row.append(member["had_pass"] if scheduled_activity.block.locked else "N/A")
                writer.writerow(row)

            return response
        else:
            return render(request, "eighth/take_attendance.html", context)


@attendance_taker_required
def accept_pass_view(request, signup_id):
    if request.method != "POST":
        return http.HttpResponseNotAllowed(["POST"], "HTTP 405: METHOD NOT ALLOWED")

    try:
        signup = EighthSignup.objects.get(id=signup_id)
    except EighthSignup.DoesNotExist:
        raise http.Http404

    sponsor = request.user.get_eighth_sponsor()
    can_accept = signup.scheduled_activity.block.locked and (
        sponsor and (sponsor in signup.scheduled_activity.get_true_sponsors()) or request.user.is_eighth_admin
    )

    if not can_accept:
        return render(request, "error/403.html", {"reason": "You do not have permission to accept this pass."}, status=403)

    status = request.POST.get("status")

    if status == "accept":
        signup.accept_pass()
    elif status == "reject":
        signup.reject_pass()

    signup.save()

    if "admin" in request.path:
        url_name = "eighth_admin_take_attendance"
    else:
        url_name = "eighth_take_attendance"

    return redirect(url_name, scheduled_activity_id=signup.scheduled_activity.id)


@attendance_taker_required
def accept_all_passes_view(request, scheduled_activity_id):
    if request.method != "POST":
        return http.HttpResponseNotAllowed(["POST"], "HTTP 405: METHOD NOT ALLOWED")

    try:
        scheduled_activity = EighthScheduledActivity.objects.get(id=scheduled_activity_id)
    except EighthScheduledActivity.DoesNotExist:
        raise http.Http404

    sponsor = request.user.get_eighth_sponsor()
    can_accept = scheduled_activity.block.locked and (sponsor and (sponsor in scheduled_activity.get_true_sponsors()) or request.user.is_eighth_admin)

    if not can_accept:
        return render(request, "error/403.html", {"reason": "You do not have permission to take accept these passes."}, status=403)

    EighthSignup.objects.filter(after_deadline=True, scheduled_activity=scheduled_activity).update(pass_accepted=True, was_absent=False)
    invalidate_obj(scheduled_activity)

    if "admin" in request.path:
        url_name = "eighth_admin_take_attendance"
    else:
        url_name = "eighth_take_attendance"

    return redirect(url_name, scheduled_activity_id=scheduled_activity.id)


def generate_roster_pdf(sched_act_ids):
    r"""Generates a PDF roster for one or more.

    :class:`EighthScheduledActivity`\s.

    Args
        sched_act_ids
            The list of IDs of the scheduled activities to show in the PDF.

    Returns a BytesIO object for the PDF.

    """

    pdf_buffer = BytesIO()
    h_margin = 1 * inch
    v_margin = 0.5 * inch
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=h_margin, leftMargin=h_margin, topMargin=v_margin, bottomMargin=v_margin)

    elements = []

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Center", alignment=TA_CENTER))
    styles.add(ParagraphStyle(name="BlockLetter", fontSize=60, leading=72, alignment=TA_CENTER))
    styles.add(ParagraphStyle(name="BlockLetterSmall", fontSize=30, leading=72, alignment=TA_CENTER))
    styles.add(ParagraphStyle(name="BlockLetterSmallest", fontSize=20, leading=72, alignment=TA_CENTER))
    styles.add(ParagraphStyle(name="ActivityAttribute", fontSize=15, leading=18, alignment=TA_RIGHT))

    for i, said in enumerate(sched_act_ids):
        sact = EighthScheduledActivity.objects.get(id=said)

        sponsor_names = sact.get_true_sponsors().values_list("first_name", "last_name")
        sponsors_str = "; ".join(l + ", " + f for f, l in sponsor_names)

        room_names = sact.get_true_rooms().values_list("name", flat=True)
        if len(room_names) == 1:
            rooms_str = "Room " + room_names[0]
        else:
            rooms_str = "Rooms: " + ", ".join(r for r in room_names)

        block_letter = sact.block.block_letter

        if len(block_letter) < 4:
            block_letter_width = 1 * inch
            block_letter_width += (0.5 * inch) * (len(block_letter) - 1)
            block_letter_style = "BlockLetter"
        elif len(block_letter) < 7:
            block_letter_width = 0.4 * inch
            block_letter_width += (0.3 * inch) * (len(block_letter) - 1)
            block_letter_style = "BlockLetterSmall"
        else:
            block_letter_width = 0.3 * inch
            block_letter_width += (0.2 * inch) * (len(block_letter) - 1)
            block_letter_style = "BlockLetterSmallest"

        header_data = [
            [
                Paragraph("<b>Activity ID: {}<br/>Scheduled ID: {}</b>".format(sact.activity.id, sact.id), styles["Normal"]),
                Paragraph(
                    "{}<br/>{}<br/>{}".format(sponsors_str, rooms_str, sact.block.date.strftime("%A, %B %-d, %Y")), styles["ActivityAttribute"]
                ),
                Paragraph(block_letter, styles[block_letter_style]),
            ]
        ]
        header_style = TableStyle(
            [
                ("VALIGN", (0, 0), (0, 0), "TOP"),
                ("VALIGN", (1, 0), (2, 0), "MIDDLE"),
                ("TOPPADDING", (0, 0), (0, 0), 15),
                ("RIGHTPADDING", (1, 0), (1, 0), 0),
            ]
        )

        elements.append(Table(header_data, style=header_style, colWidths=[2 * inch, None, block_letter_width]))
        elements.append(Spacer(0, 10))
        elements.append(Paragraph(sact.full_title, styles["Title"]))

        num_members = sact.members.count()
        num_members_label = "{} Student{}".format(num_members, "s" if num_members != 1 else "")
        elements.append(Paragraph(num_members_label, styles["Center"]))
        elements.append(Spacer(0, 5))

        attendance_data = [
            [Paragraph("Present", styles["Heading5"]), Paragraph("Student Name (ID)", styles["Heading5"]), Paragraph("Grade", styles["Heading5"])]
        ]

        members = []
        for member in sact.members.all():
            members.append(
                (
                    member.last_name + ", " + member.first_name,
                    (member.student_id if member.student_id else "User {}".format(member.id)),
                    int(member.grade) if member.grade else "?",
                )
            )
        members = sorted(members)

        for member_name, member_id, member_grade in members:
            row = ["", "{} ({})".format(member_name, member_id), member_grade]
            attendance_data.append(row)

        # Line commands are like this:
        # op, start, stop, weight, colour, cap, dashes, join, linecount, linespacing
        attendance_style = TableStyle(
            [
                ("LINEABOVE", (0, 1), (2, 1), 1, colors.black, None, None, None, 2),
                ("LINEBELOW", (0, 1), (0, len(attendance_data)), 1, colors.black),
                ("TOPPADDING", (0, 1), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
            ]
        )

        elements.append(Table(attendance_data, style=attendance_style, colWidths=[1.3 * inch, None, 0.8 * inch]))
        elements.append(Spacer(0, 15))
        # NOTE: We should really not be writing raw HTML
        instructions = """
        <b>Highlight or circle</b> the names of students who are <b>absent</b>, and put an <b>"X"</b> next to those <b>present</b>.<br/>
        If a student arrives and their name is not on the roster, please send them to the <b>8th Period Office</b>.<br/>
        If a student leaves your activity early, please make a note. <b>Do not make any additions to the roster.</b><br/>
        Before leaving for the day, return the roster and any passes to 8th Period coordinator, {}'s mailbox in the
        <b>main office</b>. For questions, please call extension 5046 or 5078. Thank you!<br/>""".format(
            escape(settings.EIGHTH_COORDINATOR_NAME)
        )

        elements.append(Paragraph(instructions, styles["Normal"]))

        if i != len(sched_act_ids) - 1:
            elements.append(PageBreak())

    def first_page(canvas, _):
        canvas.setTitle("Eighth Activity Roster")
        canvas.setAuthor("Generated by Ion")

    doc.build(elements, onFirstPage=first_page)
    return pdf_buffer


@login_required
@deny_restricted
def eighth_absences_view(request, user_id=None):
    if user_id and request.user.is_eighth_admin:
        user = get_object_or_404(get_user_model(), id=user_id)
    elif "user" in request.GET and request.user.is_eighth_admin:
        user = get_object_or_404(get_user_model(), id=request.GET["user"])
    else:
        if request.user.is_student:
            user = request.user
        else:
            return redirect("eighth_admin_dashboard")

    absences = (
        EighthSignup.objects.filter(user=user, was_absent=True, scheduled_activity__attendance_taken=True)
        .select_related("scheduled_activity__block", "scheduled_activity__activity")
        .order_by("scheduled_activity__block")
    )
    context = {"absences": absences, "user": user}
    return render(request, "eighth/absences.html", context)


@login_required
@deny_restricted
def sponsor_schedule_widget_view(request):
    user = request.user
    eighth_sponsor = user.get_eighth_sponsor()
    num_blocks = 6
    surrounding_blocks = None
    date = None
    if "date" in request.GET:
        date = decode_date(request.GET.get("date"))
        if date:
            block = EighthBlock.objects.filter(date__gte=date).first()
            if block:
                surrounding_blocks = [block] + list(block.next_blocks(num_blocks - 1))
            else:
                surrounding_blocks = []

    if surrounding_blocks is None:
        surrounding_blocks = EighthBlock.objects.get_upcoming_blocks(num_blocks)

    context = {}

    if eighth_sponsor:
        sponsor_sch = gen_sponsor_schedule(user, eighth_sponsor, num_blocks, surrounding_blocks, date)
        context.update(sponsor_sch)
        # "sponsor_schedule", "no_attendance_today", "num_attendance_acts",
        # "sponsor_schedule_cur_date", "sponsor_schedule_prev_date", "sponsor_schedule_next_date"

    context.update({"eighth_sponsor": eighth_sponsor})

    return render(request, "eighth/sponsor_widget.html", context)


@login_required
@deny_restricted
def email_students_view(request, scheduled_activity_id):
    scheduled_activity = get_object_or_404(EighthScheduledActivity, id=scheduled_activity_id)

    if not scheduled_activity.user_is_sponsor(request.user) and not request.user.is_eighth_admin:
        raise Http404

    if request.method == "POST" and request.POST.get("body"):
        subject = settings.EMAIL_SUBJECT_PREFIX + "{}: Message from {}".format(scheduled_activity, request.user.full_name)
        if request.POST.get("subject"):
            subject += ": " + request.POST["subject"]

        body = """{} has requested to send you the following email regarding {}:\n\n{}""".format(
            request.user.full_name, scheduled_activity.activity, request.POST["body"]
        )

        email_scheduled_activity_students_task.delay(
            scheduled_activity_id=scheduled_activity_id, sender_id=request.user.id, subject=subject, body=body,
        )

        messages.success(request, "Email sent.")
        return redirect("eighth_take_attendance", scheduled_activity_id)

    context = {"scheduled_activity": scheduled_activity}

    return render(request, "eighth/email_students.html", context)
