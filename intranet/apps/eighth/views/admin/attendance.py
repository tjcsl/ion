# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import csv
from datetime import date, MINYEAR, MAXYEAR, datetime, timedelta
from django import http
from django.db.models import Count
from django.shortcuts import render
from ....auth.decorators import eighth_admin_required
from ....users.models import User
from ...models import EighthSignup
from ...utils import get_start_date


@eighth_admin_required
def delinquent_students_view(request, download_csv=None):
    lower_absence_limit = request.GET.get("lower", "")
    upper_absence_limit = request.GET.get("upper", "")

    include_freshmen = (request.GET.get("freshmen", "off") == "on")
    include_sophomores = (request.GET.get("sophomores", "off") == "on")
    include_juniors = (request.GET.get("juniors", "off") == "on")
    include_seniors = (request.GET.get("seniors", "off") == "on")

    if not request.META["QUERY_STRING"]:
        include_freshmen = True
        include_sophomores = True
        include_juniors = True
        include_seniors = True

    start_date = request.GET.get("start", "")
    end_date = request.GET.get("end", "")

    if not lower_absence_limit.isdigit():
        lower_absence_limit = ""
        lower_absence_limit_filter = 0
    else:
        lower_absence_limit_filter = lower_absence_limit

    if not upper_absence_limit.isdigit():
        upper_absence_limit = ""
        upper_absence_limit_filter = 1000
    else:
        upper_absence_limit_filter = upper_absence_limit

    try:
        start_date = datetime.strptime(start_date, "%m/%d/%Y")
        start_date_filter = start_date
    except ValueError:
        start_date = ""
        start_date_filter = date(MINYEAR, 1, 1)

    try:
        end_date = datetime.strptime(end_date, "%m/%d/%Y")
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
        "include_seniors":  include_seniors,
        "start_date": start_date,
        "end_date": end_date,
    }

    query_params = ["lower",
                    "upper",
                    "freshmen",
                    "sophomores",
                    "juniors",
                    "seniors",
                    "start",
                    "end"]

    if set(request.GET.keys()).intersection(set(query_params)):
        delinquents = EighthSignup.objects \
                                  .filter(was_absent=True,
                                          scheduled_activity__block__date__gte=start_date_filter,
                                          scheduled_activity__block__date__lte=end_date_filter) \
                                  .values("user") \
                                  .annotate(absences=Count("user")) \
                                  .filter(absences__gte=lower_absence_limit_filter,
                                          absences__lte=upper_absence_limit_filter) \
                                  .values("user", "absences") \
                                  .order_by("user")

        user_ids = [d["user"] for d in delinquents]
        delinquent_users = User.objects.filter(id__in=user_ids).order_by("id")
        for index, user in enumerate(delinquent_users):
            delinquents[index]["user"] = user

        def filter_by_grade(delinquent):
            grade = delinquent["user"].grade.number()
            include = False
            if include_freshmen:
                include |= (grade == 9)
            if include_sophomores:
                include |= (grade == 10)
            if include_juniors:
                include |= (grade == 11)
            if include_seniors:
                include |= (grade == 12)
            return include

        delinquents = filter(filter_by_grade, delinquents)
        context["delinquents"] = delinquents
    else:
        delinquents = []

    if request.resolver_match.url_name == "eighth_admin_view_delinquent_students":
        context["admin_page_title"] = "Delinquent Students"
        return render(request, "eighth/admin/delinquent_students.html", context)
    else:
        response = http.HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=\"delinquent_students.csv\""

        writer = csv.writer(response)
        writer.writerow(["Absences",
                         "Last Name",
                         "First Name",
                         "Student ID",
                         "Grade",
                         "Counselor"])

        for delinquent in delinquents:
            row = []
            row.append(delinquent["absences"])
            row.append(delinquent["user"].last_name)
            row.append(delinquent["user"].first_name)
            row.append(delinquent["user"].student_id)
            row.append(delinquent["user"].grade.number())
            counselor = delinquent["user"].counselor
            row.append(counselor.last_name if counselor else "")
            writer.writerow(row)

        return response


@eighth_admin_required
def after_deadline_signup_view(request):
    start_date = request.GET.get("start", "")
    end_date = request.GET.get("end", "")

    try:
        start_date = datetime.strptime(start_date, "%m/%d/%Y")
    except ValueError:
        start_date = get_start_date(request)

    try:
        end_date = datetime.strptime(end_date, "%m/%d/%Y")
    except ValueError:
        end_date = start_date + timedelta(days=7)

    signups = EighthSignup.objects \
                          .filter(after_deadline=True,
                                  time__gte=start_date,
                                  time__lte=end_date) \
                          .order_by("time")

    context = {
        "admin_page_title": "After Deadline Signups",
        "signups": signups,
        "start_date": start_date,
        "end_date": end_date
    }

    return render(request, "eighth/admin/after_deadline_signups.html", context)
