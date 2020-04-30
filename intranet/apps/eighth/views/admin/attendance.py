import csv
import logging
from datetime import MAXYEAR, MINYEAR, date, datetime, timedelta

from cacheops import invalidate_obj

from django import http
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.shortcuts import redirect, render

from .....utils.helpers import is_entirely_digit
from ....auth.decorators import eighth_admin_required
from ...models import EighthActivity, EighthBlock, EighthRoom, EighthScheduledActivity, EighthSignup
from ...utils import get_start_date

logger = logging.getLogger(__name__)


@eighth_admin_required
def delinquent_students_view(request):
    lower_absence_limit = request.GET.get("lower", "")
    upper_absence_limit = request.GET.get("upper", "")

    include_freshmen = request.GET.get("freshmen", "off") == "on"
    include_sophomores = request.GET.get("sophomores", "off") == "on"
    include_juniors = request.GET.get("juniors", "off") == "on"
    include_seniors = request.GET.get("seniors", "off") == "on"

    if not request.META["QUERY_STRING"]:
        include_freshmen = True
        include_sophomores = True
        include_juniors = True
        include_seniors = True

    start_date = request.GET.get("start", "")
    end_date = request.GET.get("end", "")

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
    }

    query_params = ["lower", "upper", "freshmen", "sophomores", "juniors", "seniors", "start", "end"]

    if set(request.GET.keys()).intersection(set(query_params)):
        # attendance MUST have been taken on the activity for the absence to be valid
        delinquents = []
        if int(upper_absence_limit_filter) > 0 and int(lower_absence_limit_filter) > 0:
            delinquents = (
                EighthSignup.objects.filter(
                    was_absent=True,
                    scheduled_activity__attendance_taken=True,
                    scheduled_activity__block__date__gte=start_date_filter,
                    scheduled_activity__block__date__lte=end_date_filter,
                )
                .values("user")
                .annotate(absences=Count("user"))
                .filter(absences__gte=lower_absence_limit_filter, absences__lte=upper_absence_limit_filter)
                # Order with most absences at top
                .order_by("user")
                .values("user", "absences")
            )

            user_ids = [d["user"] for d in delinquents]
            delinquent_users = get_user_model().objects.filter(id__in=user_ids).order_by("id")

            for index, user in enumerate(delinquent_users):
                delinquents[index]["user"] = user

            delinquents = list(delinquents)

        def filter_by_grade(delinquent):
            grade = delinquent["user"].grade.number
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

        delinquents = list(filter(filter_by_grade, delinquents))
        delinquents = sorted(delinquents, key=lambda x: (-1 * x["absences"], x["user"].last_name))
    else:
        delinquents = None

    context["delinquents"] = delinquents

    if request.resolver_match.url_name == "eighth_admin_view_delinquent_students":
        context["admin_page_title"] = "Delinquent Students"
        return render(request, "eighth/admin/delinquent_students.html", context)
    else:
        response = http.HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="delinquent_students.csv"'

        writer = csv.writer(response)
        writer.writerow(
            ["Start Date", "End Date", "Absences", "Last Name", "First Name", "Student ID", "Grade", "Counselor", "TJ Email", "Personal Email"]
        )

        for delinquent in delinquents:
            row = []
            row.append(str(start_date).split(" ", 1)[0])
            row.append(str(end_date).split(" ", 1)[0])
            row.append(delinquent["absences"])
            row.append(delinquent["user"].last_name)
            row.append(delinquent["user"].first_name)
            row.append(delinquent["user"].student_id)
            row.append(delinquent["user"].grade.number)
            counselor = delinquent["user"].counselor
            row.append(counselor.last_name if counselor else "")
            row.append(delinquent["user"].tj_email)
            row.append(delinquent["user"].non_tj_email or "")
            writer.writerow(row)

        return response


@eighth_admin_required
def no_signups_roster(request, block_id):
    try:
        block = EighthBlock.objects.get(id=block_id)
    except EighthBlock.DoesNotExist:
        raise http.Http404

    unsigned = block.get_unsigned_students()
    unsigned = sorted(unsigned, key=lambda u: (u.last_name, u.first_name))

    user_signups_hidden = block.get_hidden_signups()

    if request.resolver_match.url_name == "eighth_admin_no_signups_roster":
        context = {"eighthblock": block, "users": unsigned, "user_signups_hidden": user_signups_hidden, "admin_page_title": "No Signups Roster"}

        return render(request, "eighth/admin/no_signups_roster.html", context)
    else:
        response = http.HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="no_signups_roster.csv"'
        writer = csv.writer(response)
        writer.writerow(["Block ID", "Block Date", "Last Name", "First Name", "Student ID", "Grade", "Counselor", "TJ Email", "Personal Email"])

        for user in unsigned:
            row = []
            row.append("{}".format(block.id))
            row.append("{}".format(block))
            row.append(user.last_name)
            row.append(user.first_name)
            row.append(user.student_id)
            row.append(user.grade.number)
            counselor = user.counselor
            row.append(counselor.last_name if counselor else "")
            row.append(user.tj_email)
            row.append(user.non_tj_email or "")
            writer.writerow(row)

        return response


@eighth_admin_required
def after_deadline_signup_view(request):
    start_date = request.GET.get("start", "")
    end_date = request.GET.get("end", "")

    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        start_date = get_start_date(request)

    try:
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        end_date = start_date + timedelta(days=7)

    signups = EighthSignup.objects.filter(after_deadline=True, time__gte=start_date, time__lte=end_date).order_by("-time")

    context = {"admin_page_title": "After Deadline Signups", "signups": signups, "start_date": start_date, "end_date": end_date}

    if request.resolver_match.url_name == "eighth_admin_download_after_deadline_signups_csv":
        response = http.HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="after_deadline_signups.csv"'

        writer = csv.writer(response)
        writer.writerow(
            [
                "Start Date",
                "End Date",
                "Time",
                "Block",
                "Last Name",
                "First Name",
                "Student ID",
                "Grade",
                "From Activity",
                "From Sponsor",
                "To Activity ID",
                "To Activity",
                "To Sponsor",
            ]
        )

        for signup in signups:
            row = []
            row.append(datetime.strftime(start_date, "%m/%d/%Y"))
            row.append(datetime.strftime(end_date, "%m/%d/%Y"))
            row.append(signup.time)
            row.append(signup.scheduled_activity.block)
            row.append(signup.user.last_name)
            row.append(signup.user.first_name)
            row.append(signup.user.student_id)
            row.append(signup.user.grade.number)
            row.append(signup.previous_activity_name)
            row.append(signup.previous_activity_sponsors)
            row.append(signup.scheduled_activity.activity.id)
            row.append(signup.scheduled_activity.activity.name_with_flags)
            row.append(" ,".join([str(sponsor) for sponsor in signup.scheduled_activity.get_true_sponsors()]))
            writer.writerow(row)

        return response

    return render(request, "eighth/admin/after_deadline_signups.html", context)


@eighth_admin_required
def activities_without_attendance_view(request):
    blocks = EighthBlock.objects.filter(date__gte=get_start_date(request))
    block_id = request.GET.get("block", None)
    block = None

    if block_id is not None:
        try:
            block = EighthBlock.objects.get(id=block_id)
        except (EighthBlock.DoesNotExist, ValueError):
            pass

    context = {"blocks": blocks, "chosen_block": block}

    if block is not None:
        start_date = get_start_date(request)
        scheduled_activities = block.eighthscheduledactivity_set.filter(block__date__gte=start_date, attendance_taken=False).order_by(
            "-activity__special", "activity__name"
        )  # float special to top

        context["scheduled_activities"] = scheduled_activities

        if request.POST.get("take_attendance_zero", False) is not False:
            zero_students = scheduled_activities.filter(members=None)
            signups = EighthSignup.objects.filter(scheduled_activity__in=zero_students)
            logger.debug(zero_students)
            if signups.count() == 0:
                zero_students.update(attendance_taken=True)
                messages.success(request, "Took attendance for {} empty activities.".format(zero_students.count()))
            else:
                messages.error(request, "Apparently there were actually {} signups. Maybe one is no longer empty?".format(signups.count()))
            return redirect("/eighth/admin/attendance/no_attendance?block={}".format(block.id))

        if request.POST.get("take_attendance_cancelled", False) is not False:
            cancelled = scheduled_activities.filter(cancelled=True)
            signups = EighthSignup.objects.filter(scheduled_activity__in=cancelled)
            logger.debug(cancelled)
            logger.debug(signups)
            signups.update(was_absent=True)
            cancelled.update(attendance_taken=True)
            messages.success(
                request, "Took attendance for {} cancelled activities. {} students marked absent.".format(cancelled.count(), signups.count())
            )
            return redirect("/eighth/admin/attendance/no_attendance?block={}".format(block.id))

    context["admin_page_title"] = "Activities That Haven't Taken Attendance"
    return render(request, "eighth/admin/activities_without_attendance.html", context)


@eighth_admin_required
def migrate_outstanding_passes_view(request):
    if request.method == "POST":
        try:
            block_id = request.POST.get("block", None)
            block = EighthBlock.objects.get(id=block_id)
        except EighthBlock.DoesNotExist:
            raise http.Http404

        activity, _ = EighthActivity.objects.get_or_create(name="Z - 8th Period Pass Not Received", deleted=False)
        activity.restricted = True
        activity.sticky = True
        activity.administrative = True

        if not activity.description:
            activity.description = "Pass received from the 8th period office was not turned in."

        activity.save()
        invalidate_obj(activity)

        pass_not_received, _ = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity)

        EighthSignup.objects.filter(scheduled_activity__block=block, after_deadline=True, pass_accepted=False).update(
            scheduled_activity=pass_not_received
        )

        messages.success(request, "Successfully migrated outstanding passes.")

        return redirect("eighth_admin_dashboard")
    else:
        blocks = EighthBlock.objects.filter(date__gte=get_start_date(request))

        context = {"admin_page_title": "Migrate Outstanding Passes", "blocks": blocks}

        return render(request, "eighth/admin/migrate_outstanding_passes.html", context)


@eighth_admin_required
def out_of_building_schedules_view(request, block_id=None):
    blocks = EighthBlock.objects.filter(date__gte=get_start_date(request))
    if block_id is None:
        block_id = request.GET.get("block", None)
    block = None

    if block_id is not None:
        try:
            block = EighthBlock.objects.get(id=block_id)
        except (EighthBlock.DoesNotExist, ValueError):
            pass

    context = {"blocks": blocks, "chosen_block": block}

    if block is not None:
        rooms = EighthRoom.objects.filter(name__icontains="out of building")

        if rooms:
            rooms_filter = Q(scheduled_activity__rooms__in=rooms) | (
                Q(scheduled_activity__rooms=None) & Q(scheduled_activity__activity__rooms__in=rooms)
            )
            signups = (
                EighthSignup.objects.filter(scheduled_activity__block=block).filter(rooms_filter).distinct().order_by("scheduled_activity__activity")
            )
            context["signups"] = signups

    if request.resolver_match.url_name == "eighth_admin_export_out_of_building_schedules":
        context["admin_page_title"] = "Export Out of Building Schedules"
        return render(request, "eighth/admin/out_of_building_schedules.html", context)
    else:
        response = http.HttpResponse(content_type="text/csv")
        block_date_str = datetime.strftime(block.date, "%m_%d_%Y")
        filename = '"out_of_building_schedules_{}.csv"'.format(block_date_str)
        response["Content-Disposition"] = "attachment; filename=" + filename

        writer = csv.writer(response)
        writer.writerow(["Last Name", "First Name", "Student ID", "Date", "Block", "Activity ID", "Activity Name"])

        for signup in signups:
            row = []
            row.append(signup.user.last_name)
            row.append(signup.user.first_name)
            row.append(signup.user.student_id)
            row.append(signup.scheduled_activity.block.date)
            row.append(signup.scheduled_activity.block.block_letter)
            row.append(signup.scheduled_activity.activity.id)
            row.append(signup.scheduled_activity.title_with_flags)
            writer.writerow(row)

        return response


@eighth_admin_required
def clear_absence_view(request, signup_id):
    if request.method == "POST":
        try:
            signup = EighthSignup.objects.get(id=signup_id)
        except (EighthSignup.DoesNotExist, ValueError):
            raise http.Http404
        signup.was_absent = False
        signup.save()
        invalidate_obj(signup)
        if "next" in request.GET:
            return redirect(request.GET["next"])
        return redirect("eighth_admin_dashboard")
    else:
        return http.HttpResponseNotAllowed(["POST"], "HTTP 405: METHOD NOT ALLOWED")


@eighth_admin_required
def open_passes_view(request):
    passes = EighthSignup.objects.filter(after_deadline=True, pass_accepted=False)
    if request.method == "POST":
        pass_ids = list(request.POST.keys())

        csrf = "csrfmiddlewaretoken"
        if csrf in pass_ids:
            pass_ids.remove(csrf)

        accepted = 0
        rejected = 0
        for signup_id in pass_ids:
            signup = EighthSignup.objects.get(id=signup_id)
            status = request.POST.get(signup_id)
            if status == "accept":
                signup.accept_pass()
                accepted += 1
            elif status == "reject":
                signup.reject_pass()
                rejected += 1
            invalidate_obj(signup)

        messages.success(request, "Accepted {} and rejected {} passes.".format(accepted, rejected))

    if request.resolver_match.url_name == "eighth_admin_view_open_passes_csv":
        response = http.HttpResponse(content_type="text/csv")
        filename = '"open_passes.csv"'
        response["Content-Disposition"] = "attachment; filename=" + filename

        writer = csv.writer(response)
        writer.writerow(["Block", "Activity", "Student", "Grade", "Absences", "Time (Last Modified)", "Time (Created)"])

        for p in passes:
            row = []
            row.append(p.scheduled_activity.block)
            row.append(p.scheduled_activity.activity)
            row.append("{}, {} {}".format(p.user.last_name, p.user.first_name, p.user.nickname if p.user.nickname else ""))
            row.append(int(p.user.grade))
            row.append(p.user.absence_count())
            row.append(p.last_modified_time)
            row.append(p.created_time)
            writer.writerow(row)

        return response

    context = {"admin_page_title": "Open Passes", "passes": passes}
    return render(request, "eighth/admin/open_passes.html", context)
