import csv
import logging
from collections import defaultdict
from datetime import MAXYEAR, MINYEAR, date, datetime, timedelta
from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from ....utils.date import get_date_range_this_year, get_senior_graduation_year
from ....utils.helpers import is_entirely_digit
from ....utils.serialization import safe_json
from ...auth.decorators import deny_restricted
from ..forms.admin.activities import ActivityMultiSelectForm
from ..models import EighthActivity, EighthBlock, EighthScheduledActivity, EighthSignup
from ..utils import get_start_date

logger = logging.getLogger(__name__)


@login_required
@deny_restricted
def activity_view(request, activity_id=None):
    activity = get_object_or_404(EighthActivity, id=activity_id)
    scheduled_activities = EighthScheduledActivity.objects.filter(activity=activity)

    show_all = "show_all" in request.GET
    if not show_all:
        first_date = timezone.localtime(timezone.now()).date()
        first_block = EighthBlock.objects.get_first_upcoming_block()
        if first_block:
            first_date = first_block.date

        two_months = timezone.localtime(timezone.now()).date() + timedelta(weeks=8)
        scheduled_activities = scheduled_activities.filter(block__date__gte=first_date, block__date__lte=two_months)

    scheduled_activities = scheduled_activities.order_by("block__date", "block__block_letter")

    context = {"activity": activity, "scheduled_activities": scheduled_activities}

    return render(request, "eighth/activity.html", context)


def chunks(items, n):
    for i in range(0, len(items), n):
        yield items[i: i + n]


def current_school_year():
    now = timezone.localtime()
    if now.month <= settings.YEAR_TURNOVER_MONTH:
        return now.year
    else:
        return now.year + 1


def generate_statistics_pdf(activities=None, start_date=None, all_years=False, year=None):
    """ Accepts EighthActivity objects and outputs a PDF file. """
    if activities is None:
        activities = EighthActivity.objects.all().order_by("name")
    if year is None:
        year = current_school_year()

    if not isinstance(activities, list):
        activities = activities.prefetch_related("rooms").prefetch_related("sponsors")

    pdf_buffer = BytesIO()

    h_margin = 1 * inch
    v_margin = 0.5 * inch
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=h_margin, leftMargin=h_margin, topMargin=v_margin, bottomMargin=v_margin)

    elements = []

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Indent", leftIndent=15))

    empty_activities = []

    for act in activities:
        lelements = []
        relements = []
        act_stats = calculate_statistics(act, start_date=start_date, all_years=all_years, year=year)
        if act_stats["total_blocks"] == 0:
            empty_activities.append(act.name)
            continue
        elements.append(Paragraph(act.name, styles["Title"]))
        sponsor_str = (", ".join([x.name for x in act.sponsors.all()])) if act.sponsors.count() > 0 else "None"
        lelements.append(Paragraph("<b>Default Sponsors:</b> " + sponsor_str, styles["Normal"]))
        lelements.append(Spacer(0, 0.025 * inch))
        room_str = (", ".join([str(x) for x in act.rooms.all()])) if act.rooms.count() > 0 else "None"
        relements.append(Paragraph("<b>Default Rooms:</b> " + room_str, styles["Normal"]))
        relements.append(Spacer(0, 0.025 * inch))

        relements.append(Paragraph("<b>Total blocks:</b> {}".format(act_stats["total_blocks"]), styles["Normal"]))
        relements.append(Paragraph("<b>Scheduled blocks:</b> {}".format(act_stats["scheduled_blocks"]), styles["Indent"]))
        relements.append(Paragraph("<b>Empty blocks:</b> {}".format(act_stats["empty_blocks"]), styles["Indent"]))
        relements.append(Paragraph("<b>Cancelled blocks:</b> {}".format(act_stats["cancelled_blocks"]), styles["Indent"]))

        lelements.append(Paragraph("<b>Total signups:</b> {}".format(act_stats["total_signups"]), styles["Normal"]))
        lelements.append(Paragraph("<b>Average signups per block:</b> {}".format(act_stats["average_signups"]), styles["Indent"]))
        lelements.append(Paragraph("<b>Average signups per student:</b> {}".format(act_stats["average_user_signups"]), styles["Indent"]))
        lelements.append(
            Paragraph("<b>Unique students:</b> {}, <b>Capacity:</b> {}".format(act_stats["students"], act_stats["capacity"]), styles["Normal"])
        )

        elements.append(
            Table(
                [[lelements, relements]],
                style=[("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("VALIGN", (0, 0), (-1, -1), "TOP")],
            )
        )

        parsed_members = [[x.username, y] for x, y in act_stats["members"]]
        parsed_members = list(chunks(parsed_members, 30))[:3]
        if parsed_members:
            parsed_members = [[["Username", "Signups"]] + x for x in parsed_members]
            parsed_members = [
                Table(x, style=[("FONT", (0, 0), (1, 0), "Helvetica-Bold"), ("ALIGN", (1, 0), (1, -1), "RIGHT")]) for x in parsed_members
            ]
            elements.append(Table([parsed_members], style=[("VALIGN", (-1, -1), (-1, -1), "TOP")]))
            if act_stats["students"] - 90 > 0:
                elements.append(Paragraph("<b>{}</b> students were not shown on this page. ".format(act_stats["students"] - 90), styles["Normal"]))
        else:
            elements.append(Spacer(0, 0.20 * inch))

        if start_date is not None:
            elements.append(
                Paragraph(
                    "<b>{}</b> block(s) are past the start date and are not included on this page.".format(act_stats["past_start_date"]),
                    styles["Normal"],
                )
            )
        elements.append(
            Paragraph(
                "<b>{}</b> block(s) not in the {}-{} school year are not included on this page.".format(act_stats["old_blocks"], year - 1, year),
                styles["Normal"],
            )
        )

        elements.append(PageBreak())

    if empty_activities:
        empty_activities = [x[:37] + "..." if len(x) > 40 else x for x in empty_activities]
        empty_activities = [[x] for x in empty_activities]
        empty_activities = list(chunks(empty_activities, 35))
        empty_activities = [[["Activity"]] + x for x in empty_activities]
        empty_activities = [
            Table(x, style=[("FONT", (0, 0), (-1, 0), "Helvetica-Bold"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]) for x in empty_activities
        ]
        for i in range(0, len(empty_activities), 2):
            elements.append(Paragraph("Empty Activities (Page {})".format(i // 2 + 1), styles["Title"]))
            if all_years:
                elements.append(Paragraph("The following activities have no 8th period blocks assigned to them.", styles["Normal"]))
            else:
                elements.append(
                    Paragraph(
                        "The following activities have no 8th period blocks assigned to them for the {}-{} school year.".format(year - 1, year),
                        styles["Normal"],
                    )
                )
            elements.append(Spacer(0, 0.10 * inch))
            ea = [empty_activities[i]]
            if i + 1 < len(empty_activities):
                ea.append(empty_activities[i + 1])
            elements.append(
                Table(
                    [ea],
                    style=[("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("VALIGN", (0, 0), (-1, -1), "TOP")],
                    hAlign="LEFT",
                )
            )
            elements.append(PageBreak())

    def first_page(canvas, _):
        if len(activities) == 1:
            canvas.setTitle("{} Statistics".format(activities[0].name))
        else:
            canvas.setTitle("8th Period Activity Statistics")
        canvas.setAuthor("Generated by Ion")

    doc.build(elements, onFirstPage=first_page)

    pdf_buffer.seek(0)

    return pdf_buffer


def calculate_statistics(activity, start_date=None, all_years=False, year=None, future=False):
    activities = EighthScheduledActivity.objects.filter(activity=activity)

    signups = defaultdict(int)
    chart_data = defaultdict(dict)

    old_blocks = 0

    if year is not None and year == get_senior_graduation_year():
        start_date = datetime.today()

    if start_date is None or future:
        filtered_activities = activities
        past_start_date = 0
    else:
        filtered_activities = activities.filter(block__date__lte=start_date)
        past_start_date = activities.count() - filtered_activities.count()

    if not all_years:
        if year is None or year == get_senior_graduation_year():
            year_start, year_end = get_date_range_this_year()
        else:
            year_start, year_end = get_date_range_this_year(datetime(year, 1, 1))
        year_filtered = filtered_activities.filter(block__date__gte=year_start, block__date__lte=year_end)
        old_blocks = filtered_activities.count() - year_filtered.count()
        filtered_activities = year_filtered

    activities = filtered_activities

    cancelled_blocks = activities.filter(cancelled=True).count()
    empty_blocks = 0

    for a in activities.filter(cancelled=False).select_related("block").prefetch_related("members"):
        members = a.members.filter(eighthsignup__was_absent=False).count()
        if members == 0:
            empty_blocks += 1
        else:
            for user in a.members.all():
                signups[user] += 1
            chart_data[str(a.block.date)][str(a.block.block_letter)] = members

    signups = sorted(signups.items(), key=lambda kv: (-kv[1], kv[0].username))

    total_blocks = activities.count()
    scheduled_blocks = total_blocks - cancelled_blocks
    total_signups = sum(n for _, n in signups)

    if scheduled_blocks:
        average_signups = round(total_signups / scheduled_blocks, 2)
    else:
        average_signups = 0

    if signups:
        average_user_signups = round(total_signups / len(signups), 2)
    else:
        average_user_signups = 0
    return {
        "members": signups,
        "students": len(signups),
        "total_blocks": total_blocks,
        "total_signups": total_signups,
        "average_signups": average_signups,
        "average_user_signups": average_user_signups,
        "old_blocks": old_blocks,
        "cancelled_blocks": cancelled_blocks,
        "scheduled_blocks": scheduled_blocks,
        "empty_blocks": empty_blocks,
        "capacity": activities[total_blocks - 1].get_true_capacity() if total_blocks > 0 else 0,
        "chart_data": safe_json(chart_data),
        "past_start_date": past_start_date,
    }


@login_required
@deny_restricted
def stats_global_view(request):
    if not request.user.is_eighth_admin:
        return render(request, "error/403.html", {"reason": "You do not have permission to generate global statistics."}, status=403)

    if request.method == "POST" and request.POST.get("year", False):
        year = int(request.POST.get("year"))
        do_csv = request.POST.get("generate", "csv") == "csv"
        if do_csv:
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = 'attachment; filename="eighth.csv"'
            writer = csv.writer(response)
            writer.writerow(
                [
                    "Activity",
                    "Default Sponsors",
                    "Default Rooms",
                    "Capacity",
                    "Unique Students",
                    "Total Blocks",
                    "Scheduled Blocks",
                    "Cancelled Blocks",
                    "Empty Blocks",
                    "Total Signups",
                    "Average Signups per Block",
                    "Average Signups per Student",
                ]
            )
            for act in EighthActivity.objects.all().order_by("name").prefetch_related("rooms").prefetch_related("sponsors"):
                stats = calculate_statistics(act, year=year)
                writer.writerow(
                    [
                        act.name,
                        ", ".join([x.name for x in act.sponsors.all()]),
                        ", ".join([str(x) for x in act.rooms.all()]),
                        stats["capacity"],
                        stats["students"],
                        stats["total_blocks"],
                        stats["scheduled_blocks"],
                        stats["cancelled_blocks"],
                        stats["empty_blocks"],
                        stats["total_signups"],
                        stats["average_signups"],
                        stats["average_user_signups"],
                    ]
                )
        else:
            response = HttpResponse(content_type="application/pdf")
            response["Content-Disposition"] = 'inline; filename="eighth.pdf"'
            buf = generate_statistics_pdf(year=year)
            response.write(buf.getvalue())
            buf.close()
        return response

    current_year = current_school_year()

    if EighthBlock.objects.count() == 0:
        earliest_year = current_year
    else:
        earliest_year = EighthBlock.objects.order_by("date").first().date.year

    context = {"years": list(reversed(range(earliest_year, current_year + 1)))}

    return render(request, "eighth/admin/global_statistics.html", context)


@login_required
@deny_restricted
def stats_multiple_view(request):
    if not request.user.is_eighth_admin:
        return render(request, "error/403.html", {"reason": "You do not have permission to view eighth activity statistics."}, status=403)

    form = None
    context = None
    if request.method == "POST":
        form = ActivityMultiSelectForm(request.POST)

        lower_absence_limit = request.POST.get("lower", "")
        upper_absence_limit = request.POST.get("upper", "")

        include_freshmen = request.POST.get("freshmen", "off") == "on"
        include_sophomores = request.POST.get("sophomores", "off") == "on"
        include_juniors = request.POST.get("juniors", "off") == "on"
        include_seniors = request.POST.get("seniors", "off") == "on"

        start_date = request.POST.get("start", "")
        end_date = request.POST.get("end", "")

        if lower_absence_limit == "" or not is_entirely_digit(lower_absence_limit):
            lower_absence_limit = "1"
            lower_absence_limit_filter = 1
        else:
            lower_absence_limit_filter = lower_absence_limit

        if upper_absence_limit == "" or not is_entirely_digit(upper_absence_limit):
            upper_absence_limit = "100"
            upper_absence_limit_filter = 100
        else:
            upper_absence_limit_filter = upper_absence_limit

        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            start_date_filter = start_date
        except ValueError:
            start_date = ""
            start_date_filter = date(MINYEAR, 1, 1)

        try:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
            end_date_filter = end_date
        except ValueError:
            end_date = ""
            end_date_filter = date(MAXYEAR, 12, 31)

        context = {
            "lower_absence_limit": lower_absence_limit,
            "upper_absence_limit": upper_absence_limit,
            "include_freshmen": include_freshmen,
            "include_sophomores": include_sophomores,
            "include_juniors": include_juniors,
            "include_seniors": include_seniors,
            "start_date": start_date,
            "end_date": end_date,
            "form": form,
            "admin_page_title": "View activity signup statistics",
        }

        if form.is_valid():
            if int(upper_absence_limit_filter) > 0 and int(lower_absence_limit_filter) > 0:
                act_ids = [act.id for act in form.cleaned_data["activities"]]

                signed_up = (
                    EighthSignup.objects.filter(
                        scheduled_activity__block__date__gte=start_date_filter,
                        scheduled_activity__block__date__lte=end_date_filter,
                        scheduled_activity__activity__id__in=act_ids,
                    )
                    .values("user")
                    .annotate(signups=Count("user"))
                    .filter(signups__gte=lower_absence_limit_filter, signups__lte=upper_absence_limit_filter)
                    .order_by("user")
                    .values("user", "signups")
                )

                user_ids = [d["user"] for d in signed_up]
                signed_up_users = get_user_model().objects.filter(id__in=user_ids).order_by("id")

                for index, user in enumerate(signed_up_users):
                    signed_up[index]["user"] = user

                signed_up = list(signed_up)

                def filter_by_grade(signed_up):
                    grade = signed_up["user"].grade.number
                    include = False
                    if include_freshmen:
                        include |= grade == 9
                    if include_sophomores:
                        include |= grade == 10
                    if include_juniors:
                        include |= grade == 11
                    if include_seniors:
                        include |= grade == 12
                    return include

                signed_up = list(filter(filter_by_grade, signed_up))
                signed_up = sorted(signed_up, key=lambda x: (-1 * x["signups"], x["user"].last_name))

                context["signed_up"] = signed_up
    else:
        form = ActivityMultiSelectForm()
        context = {"form": form, "admin_page_title": "View activity signup statistics"}

    return render(request, "eighth/admin/multiple_statistics.html", context=context)


@login_required
@deny_restricted
def stats_view(request, activity_id=None):
    """If a the GET parameter `year` is set, it uses stats from given year
    with the following caveats:
        - If it's the current year and start_date is set, start_date is ignored
        - If it's the current year, stats will only show up to today - they won't
          go into the future.
    `all_years` (obviously) displays all years.
    """
    if not (request.user.is_eighth_admin or request.user.is_teacher):
        return render(request, "error/403.html", {"reason": "You do not have permission to view statistics for this activity."}, status=403)

    activity = get_object_or_404(EighthActivity, id=activity_id)

    if request.GET.get("print", False):
        response = HttpResponse(content_type="application/pdf")
        buf = generate_statistics_pdf([activity], year=int(request.GET.get("year", 0)) or None)
        response.write(buf.getvalue())
        buf.close()
        return response

    current_year = current_school_year()

    if EighthBlock.objects.count() == 0:
        earliest_year = current_year
    else:
        earliest_year = EighthBlock.objects.order_by("date").first().date.year

    if request.GET.get("year", False):
        year = int(request.GET.get("year"))
    else:
        year = None

    future = request.GET.get("future", False)

    context = {"activity": activity, "years": list(reversed(range(earliest_year, current_year + 1))), "year": year, "future": future}

    if year:
        context.update(calculate_statistics(activity, year=year, future=future))
    else:
        context.update(calculate_statistics(activity, get_start_date(request), future=future))
    return render(request, "eighth/statistics.html", context)
