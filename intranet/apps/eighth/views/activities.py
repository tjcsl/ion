# -*- coding: utf-8 -*-

import logging
from collections import defaultdict
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse

from ..models import EighthActivity, EighthBlock, EighthScheduledActivity
from ..utils import get_start_date
from ....utils.date import get_date_range_this_year
from ....utils.serialization import safe_json

from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table

logger = logging.getLogger(__name__)


@login_required
def activity_view(request, activity_id=None):
    activity = get_object_or_404(EighthActivity, id=activity_id)
    first_block = EighthBlock.objects.get_first_upcoming_block()
    scheduled_activities = EighthScheduledActivity.objects.filter(activity=activity)

    show_all = ("show_all" in request.GET)
    if first_block and not show_all:
        two_months = datetime.now().date() + timedelta(weeks=8)
        scheduled_activities = scheduled_activities.filter(block__date__gte=first_block.date, block__date__lte=two_months)

    scheduled_activities = scheduled_activities.order_by("block__date")

    context = {"activity": activity, "scheduled_activities": scheduled_activities}

    return render(request, "eighth/activity.html", context)


def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


def current_school_year():
    if datetime.now().month <= settings.YEAR_TURNOVER_MONTH:
        return datetime.now().year
    else:
        return datetime.now().year + 1


def generate_statistics_pdf(activities=None, start_date=None, all_years=False, year=None):
    ''' Accepts EighthActivity objects and outputs a PDF file. '''
    if activities is None:
        activities = EighthActivity.objects.all().order_by("name")
    if year is None:
        year = current_school_year()

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
        lelements.append(Paragraph("<b>Unique students:</b> {}, <b>Capacity:</b> {}".format(act_stats["students"], act_stats["capacity"]), styles["Normal"]))

        elements.append(Table([[lelements, relements]], style=[
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))

        parsed_members = [[x.username, y] for x, y in act_stats["members"]]
        parsed_members = list(chunks(parsed_members, 30))[:3]
        if parsed_members:
            parsed_members = [[["Username", "Signups"]] + x for x in parsed_members]
            parsed_members = [Table(x, style=[('FONT', (0, 0), (1, 0), 'Helvetica-Bold'), ('ALIGN', (1, 0), (1, -1), 'RIGHT')]) for x in parsed_members]
            elements.append(Table([parsed_members], style=[('VALIGN', (-1, -1), (-1, -1), 'TOP')]))
            if act_stats["students"] - 90 > 0:
                elements.append(Paragraph("<b>{}</b> students were not shown on this page. ".format(act_stats["students"] - 90), styles["Normal"]))
        else:
            elements.append(Spacer(0, 0.20 * inch))

        if start_date is not None:
            elements.append(Paragraph("<b>{}</b> block(s) are past the start date and are not included on this page.".format(act_stats["past_start_date"]), styles["Normal"]))
        elements.append(Paragraph("<b>{}</b> block(s) not in the {}-{} school year are not included on this page.".format(act_stats["old_blocks"], year - 1, year), styles["Normal"]))

        elements.append(PageBreak())

    if empty_activities:
        empty_activities = [x[:37] + "..." if len(x) > 40 else x for x in empty_activities]
        empty_activities = [[x] for x in empty_activities]
        empty_activities = list(chunks(empty_activities, 35))
        empty_activities = [[["Activity"]] + x for x in empty_activities]
        empty_activities = [Table(x, style=[
            ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0)
        ]) for x in empty_activities]
        for i in range(0, len(empty_activities), 2):
            elements.append(Paragraph("Empty Activities (Page {})".format(i//2 + 1), styles["Title"]))
            if all_years:
                elements.append(Paragraph("The following activities have no 8th period blocks assigned to them.", styles["Normal"]))
            else:
                elements.append(Paragraph("The following activities have no 8th period blocks assigned to them for the {}-{} school year.".format(year - 1, year), styles["Normal"]))
            elements.append(Spacer(0, 0.10 * inch))
            ea = [empty_activities[i]]
            if i + 1 < len(empty_activities):
                ea.append(empty_activities[i + 1])
            elements.append(Table([ea], style=[
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ], hAlign='LEFT'))
            elements.append(PageBreak())

    def firstPage(canvas, doc):
        if len(activities) == 1:
            canvas.setTitle("{} Statistics".format(activities[0].name))
        else:
            canvas.setTitle("8th Period Activity Statistics")
        canvas.setAuthor("Generated by Ion")

    doc.build(elements, onFirstPage=firstPage)

    pdf_buffer.seek(0)

    return pdf_buffer


def calculate_statistics(activity, start_date=None, all_years=False, year=None):
    activities = EighthScheduledActivity.objects.filter(activity=activity)

    signups = defaultdict(int)
    chart_data = defaultdict(dict)

    old_blocks = 0

    if start_date is None:
        filtered_activities = activities
        past_start_date = 0
    else:
        filtered_activities = activities.filter(block__date__lte=start_date)
        past_start_date = activities.count() - filtered_activities.count()

    if not all_years:
        if year is None:
            year_start, year_end = get_date_range_this_year()
        else:
            year_start, year_end = get_date_range_this_year(datetime(year, 1, 1))
        year_filtered = filtered_activities.filter(block__date__gte=year_start, block__date__lte=year_end)
        old_blocks = filtered_activities.count() - len(year_filtered)
        filtered_activities = year_filtered

    activities = filtered_activities

    cancelled_blocks = activities.filter(cancelled=True).count()
    empty_blocks = 0

    for a in activities.filter(cancelled=False):
        members = a.members.count()
        if members == 0:
            empty_blocks += 1
        else:
            for user in a.members.all():
                signups[user] += 1
            chart_data[str(a.block.date)][str(a.block.block_letter)] = members

    signups = sorted(signups.items(), key=lambda kv: (-kv[1], kv[0].username))

    total_blocks = len(activities)
    scheduled_blocks = total_blocks - cancelled_blocks
    total_signups = sum(n for _, n in signups)

    if scheduled_blocks:
        average_signups = round(total_signups / scheduled_blocks, 2)
    else:
        average_signups = 0

    if len(signups) > 0:
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
        "past_start_date": past_start_date
    }


@login_required
def stats_global_view(request):
    if not request.user.is_eighth_admin:
        return render(request, "error/403.html", {"reason": "You do not have permission to generate global statistics."}, status=403)

    if request.method == "POST" and request.POST.get("year", False):
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = 'inline; filename="eighth.pdf"'
        year = int(request.POST.get("year"))
        buf = generate_statistics_pdf(year=year)
        response.write(buf.getvalue())
        buf.close()
        return response

    current_year = current_school_year()

    if EighthBlock.objects.count() == 0:
        earliest_year = current_year
    else:
        earliest_year = EighthBlock.objects.order_by("date").first().date.year

    context = {
        "years": list(reversed(range(earliest_year, current_year + 1)))
    }

    return render(request, "eighth/admin/global.html", context)


@login_required
def stats_view(request, activity_id=None):
    if not (request.user.is_eighth_admin or request.user.is_teacher):
        return render(request, "error/403.html", {"reason": "You do not have permission to view statistics for this activity."}, status=403)

    activity = get_object_or_404(EighthActivity, id=activity_id)

    if request.GET.get("print", False):
        response = HttpResponse(content_type="application/pdf")
        buf = generate_statistics_pdf([activity])
        response.write(buf.getvalue())
        buf.close()
        return response

    context = {"activity": activity}
    context.update(calculate_statistics(activity, get_start_date(request)))
    return render(request, "eighth/statistics.html", context)
