# -*- coding: utf-8 -*-

import logging
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse

from ..models import EighthActivity, EighthBlock, EighthScheduledActivity
from ..utils import get_start_date
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


def generate_statistics_pdf(activities=None, start_date=None, all_years=False):
    ''' Accepts EighthActivity objects and outputs a PDF file. '''
    if activities is None:
        activities = EighthActivity.objects.all()

    pdf_buffer = BytesIO()

    h_margin = 1 * inch
    v_margin = 0.5 * inch
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=h_margin, leftMargin=h_margin, topMargin=v_margin, bottomMargin=v_margin)

    elements = []

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Indent", leftIndent=15))

    for act in activities:
        lelements = []
        relements = []
        elements.append(Paragraph(act.name, styles["Title"]))
        sponsor_str = (", ".join([x.name for x in act.sponsors.all()])) if act.sponsors.count() > 0 else "None"
        lelements.append(Paragraph("<b>Default Sponsors:</b> " + sponsor_str, styles["Normal"]))
        lelements.append(Spacer(0, 0.025 * inch))
        room_str = (", ".join([str(x) for x in act.rooms.all()])) if act.rooms.count() > 0 else "None"
        relements.append(Paragraph("<b>Default Rooms:</b> " + room_str, styles["Normal"]))
        relements.append(Spacer(0, 0.025 * inch))

        act_stats = calculate_statistics(act, start_date=start_date, all_years=all_years)
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

        elements.append(Paragraph("<b>{}</b> block(s) are past the start date and are not included on this page.".format(act_stats["past_start_date"]), styles["Normal"]))
        elements.append(Paragraph("<b>{}</b> block(s) from previous years are not included on this page.".format(act_stats["old_blocks"]), styles["Normal"]))

        elements.append(PageBreak())

    def firstPage(canvas, doc):
        if len(activities) == 1:
            canvas.setTitle("{} Statistics".format(activities[0].name))
        else:
            canvas.setTitle("Eighth Period Activity Statistics")
        canvas.setAuthor("Generated by Ion")

    doc.build(elements, onFirstPage=firstPage)

    pdf_buffer.seek(0)

    return pdf_buffer


def calculate_statistics(activity, start_date=None, all_years=False):
    if not start_date:
        start_date = datetime.now().date()

    activities = EighthScheduledActivity.objects.filter(activity=activity)

    signups = {}
    chart_data = {}

    old_blocks = 0
    cancelled_blocks = 0
    empty_blocks = 0

    past_start_date = 0

    filtered_activities = []

    for a in activities:
        if a.block.is_this_year or all_years:
            if a.block.date > start_date:
                past_start_date += 1
                continue
            filtered_activities.append(a)
        else:
            old_blocks += 1

    activities = filtered_activities

    for a in activities:
        if a.cancelled:
            cancelled_blocks += 1
        else:
            members = a.members.count()
            for user in a.members.all():
                if user in signups:
                    signups[user] += 1
                else:
                    signups[user] = 1
            if str(a.block.date) not in chart_data:
                chart_data[str(a.block.date)] = {}
            chart_data[str(a.block.date)][str(a.block.block_letter)] = members
            if members == 0 and not a.cancelled:
                empty_blocks += 1

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
def statistics_view(request, activity_id=None):
    if not (request.user.is_eighth_admin or request.user.is_teacher):
        return render(request, "error/403.html", {"reason": "You do not have permission to view statistics for this activity."}, status=403)

    activity = get_object_or_404(EighthActivity, id=activity_id)

    if request.GET.get("print", False):
        response = HttpResponse(content_type="application/pdf")
        response.write(generate_statistics_pdf([activity]).getvalue())
        return response

    context = {"activity": activity}
    context.update(calculate_statistics(activity, get_start_date(request)))
    return render(request, "eighth/statistics.html", context)
