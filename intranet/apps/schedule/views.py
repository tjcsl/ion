import calendar
import logging
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_exempt

from ..auth.decorators import deny_restricted
from .forms import DayForm, DayTypeForm
from .models import Block, Day, DayType, Time

logger = logging.getLogger(__name__)
schedule_admin_required = user_passes_test(lambda u: not u.is_anonymous and u.has_admin_permission("schedule"))


def date_format(date):
    try:
        d = date.strftime("%Y-%m-%d")
    except ValueError:
        return None
    return d


def decode_date(date):
    try:
        d = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return None
    return d


def is_weekday(date):
    return date.isoweekday() in range(1, 6)


def schedule_context(request=None, date=None, use_cache=True, show_tomorrow=True):
    monday = 1
    friday = 5
    if request and "date" in request.GET:
        date = decode_date(request.GET["date"])

    if date is None:
        date = timezone.localtime()

        if is_weekday(date) and date.hour > 17 and show_tomorrow:
            delta = 3 if date.isoweekday() == friday else 1
            date += timedelta(days=delta)
        else:
            while not is_weekday(date):
                date += timedelta(days=1)

    date_fmt = date_format(date)
    key = "bell_schedule:{}".format(date_fmt)
    cached = cache.get(key)
    if cached and use_cache:
        return cached
    else:
        try:
            dayobj = Day.objects.select_related("day_type").get(date=date)
            comment = dayobj.comment
        except Day.DoesNotExist:
            dayobj = None
            comment = None

        if dayobj is not None:
            blocks = dayobj.day_type.blocks.select_related("start", "end").order_by("start__hour", "start__minute")
        else:
            blocks = []

        try:
            delta = 3 if date.isoweekday() == friday else 1
            date_tomorrow = date_format(date + timedelta(days=delta))

            date_today = date_format(date)

            delta = -3 if date.isoweekday() == monday else -1
            date_yesterday = date_format(date + timedelta(days=delta))
        except OverflowError:
            date_tomorrow = None
            date_yesterday = None
            date_today = None
            schedule_tomorrow = None

        if request and request.user.is_authenticated and request.user.is_eighth_admin:
            try:
                schedule_tomorrow = Day.objects.select_related("day_type").get(date=date_tomorrow)
                if not schedule_tomorrow.day_type:
                    schedule_tomorrow = False
            except Day.DoesNotExist:
                schedule_tomorrow = False
        else:
            schedule_tomorrow = None

        data = {
            "sched_ctx": {
                "dayobj": dayobj,
                "blocks": blocks,
                "date": date,
                "is_weekday": is_weekday(date),
                "date_tomorrow": date_tomorrow,
                "date_today": date_today,
                "date_yesterday": date_yesterday,
                "schedule_tomorrow": schedule_tomorrow,
                "comment": comment,
            }
        }
        cache.set(key, data, timeout=settings.CACHE_AGE["bell_schedule"])
        return data


# does NOT require login


def schedule_view(request):
    data = schedule_context(request)
    return render(request, "schedule/view.html", data)


# does NOT require login


def week_data(request, date=None):
    if request:
        given_date = schedule_context(request)["sched_ctx"]["date"]
        if given_date.isoweekday() not in range(1, 6):
            start_date = given_date + timedelta(days=-given_date.weekday(), weeks=1)
        else:
            start_date = given_date - timedelta(days=given_date.weekday())
    else:
        given_date = date
        if given_date.isoweekday() not in range(1, 6):
            start_date = given_date + timedelta(days=-given_date.weekday(), weeks=1)
        else:
            start_date = given_date - timedelta(days=given_date.weekday())
    days = []
    for i in range(5):
        new_date = start_date + timedelta(days=i)
        days.append(schedule_context(date=new_date))
    next_week = days[-1]["sched_ctx"]["date_tomorrow"]
    last_week = date_format(days[0]["sched_ctx"]["date"] - timedelta(days=7))
    today = date_format(timezone.localtime())
    data = {"days": days, "next_week": next_week, "last_week": last_week, "today": today}
    return data


def month_data(request):
    if request and "date" in request.GET:
        first_date = decode_date(request.GET["date"]) + relativedelta(day=1)
    else:
        first_date = timezone.now() + relativedelta(day=1)
    week1 = week_data(None, first_date)
    week2 = week_data(None, decode_date(week1["next_week"]))
    week3 = week_data(None, decode_date(week2["next_week"]))
    week4 = week_data(None, decode_date(week3["next_week"]))
    week5 = week_data(None, decode_date(week4["next_week"]))
    month = first_date.strftime("%B")
    one_month = relativedelta(months=1)
    next_month = date_format(first_date + one_month)
    last_month = date_format(first_date - one_month)
    data = {"weeks": [week1, week2, week3, week4, week5], "next_month": next_month, "last_month": last_month, "current_month": month}
    return data


@login_required
def calendar_view(request):
    data = {}
    data["week_data"] = week_data(request)
    data["month_data"] = month_data(request)
    if "view" in request.GET and request.GET["view"] == "month":
        data["view"] = "month"
    else:
        data["view"] = "week"
    return render(request, "schedule/calendar.html", data)

    # does NOT require login


@xframe_options_exempt
def schedule_embed(request):
    data = schedule_context(request)
    return render(request, "schedule/embed.html", data)


# DOES require login


@login_required
def schedule_widget_view(request):
    data = schedule_context(request)
    return render(request, "schedule/widget.html", data)


def get_day_data(firstday, daynum):
    if daynum == 0:
        return {"empty": True}

    date = firstday + timedelta(days=daynum - 1)
    data = {"day": daynum, "formatted_date": date_format(date), "date": date}

    try:
        dayobj = Day.objects.get(date=date)
        data["schedule"] = dayobj.day_type
        data["dayobj"] = dayobj
    except Day.DoesNotExist:
        data["schedule"] = None
        data["dayobj"] = None

    return data


@schedule_admin_required
@deny_restricted
def do_default_fill(request):
    """Change all Mondays to 'Anchor Day' Change all Tuesday/Thursdays to 'Blue Day' Change all
    Wednesday/Fridays to 'Red Day'."""
    monday = 0
    tuesday = 1
    wednesday = 2
    thursday = 3
    friday = 4
    try:
        anchor_day = DayType.objects.get(name="Anchor Day")
        blue_day = DayType.objects.get(name="Blue Day")
        red_day = DayType.objects.get(name="Red Day")
    except DayType.DoesNotExist:
        return render(
            request,
            "schedule/fill.html",
            {"msgs": ["Failed to insert any schedules.", "Make sure you have DayTypes defined for Anchor Days, Blue Days, and Red Days."]},
        )

    daymap = {monday: anchor_day, tuesday: blue_day, wednesday: red_day, thursday: blue_day, friday: red_day}

    msgs = []

    month = request.POST.get("month")
    firstday = datetime.strptime(month, "%Y-%m")

    yr, mn = month.split("-")
    cal = calendar.monthcalendar(int(yr), int(mn))
    for w in cal:
        for d in w:
            day = get_day_data(firstday, d)

            if "empty" in day:
                continue

            if "schedule" not in day or day["schedule"] is None:
                day_of_week = day["date"].weekday()
                if day_of_week in daymap:
                    type_obj = daymap[day_of_week]

                    day_obj = Day.objects.create(date=day["formatted_date"], day_type=type_obj)
                    msg = "{} is now a {}".format(day["formatted_date"], day_obj.day_type)
                    msgs.append(msg)
    return render(request, "schedule/fill.html", {"msgs": msgs})


def delete_cache():
    cache.delete_pattern("bell_schedule:*")
    logger.debug("Deleted bell schedule cache.")


@schedule_admin_required
@deny_restricted
def admin_home_view(request):
    if "default_fill" in request.POST:
        return do_default_fill(request)

    if "delete_cache" in request.POST:
        delete_cache()
        messages.success(request, "Deleted schedule cache manually")
        return redirect("schedule_admin")

    if "month" in request.GET:
        month = request.GET.get("month")
    elif "schedule_month" in request.session:
        month = request.session["schedule_month"]
    else:
        month = timezone.localtime().strftime("%Y-%m")

    request.session["schedule_month"] = month

    firstday = datetime.strptime(month, "%Y-%m")
    month_name = firstday.strftime("%B")
    year_name = firstday.strftime("%Y")

    yr, mn = month.split("-")
    cal = calendar.monthcalendar(int(yr), int(mn))
    sch = []
    for w in cal:
        week = []
        for d in w:
            week.append(get_day_data(firstday, d))
        sch.append(week)

    add_form = DayForm()

    this_month = firstday.strftime("%Y-%m")
    next_month = (firstday + timedelta(days=31)).strftime("%Y-%m")
    last_month = (firstday + timedelta(days=-31)).strftime("%Y-%m")

    daytypes = DayType.objects.all()

    data = {
        "month_name": month_name,
        "year_name": year_name,
        "sch": sch,
        "add_form": add_form,
        "this_month": this_month,
        "next_month": next_month,
        "last_month": last_month,
        "daytypes": daytypes,
    }

    return render(request, "schedule/admin_home.html", data)


@schedule_admin_required
@deny_restricted
def admin_add_view(request):
    if request.method == "POST":
        delete_cache()
        date = request.POST.get("date")
        day = Day.objects.filter(date=date)
        if len(day) <= 1:
            day.delete()
        form = DayForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "{} is now a {}".format(date, form.cleaned_data["day_type"]))
            return redirect("schedule_admin")
        else:
            messages.success(request, "{} has no schedule assigned".format(date))
            return redirect("schedule_admin")
    else:
        form = DayForm()

    context = {"form": form}
    return render(request, "schedule/admin_add.html", context)


@schedule_admin_required
@deny_restricted
def admin_comment_view(request):
    date = request.GET.get("date")
    if request.method == "POST" and "comment" in request.POST:
        delete_cache()
        date = request.POST.get("date")
        comment = request.POST.get("comment")
        day, _ = Day.objects.get_or_create(date=date)
        day.comment = comment
        day.save()
        return redirect("schedule_admin")
    else:
        try:
            day = Day.objects.get(date=date)
            comment = day.comment
        except Day.DoesNotExist:
            day = None
            comment = None

    context = {"day": day, "date": date, "comment": comment}

    return render(request, "schedule/admin_comment.html", context)


@schedule_admin_required
@deny_restricted
def admin_daytype_view(request, daytype_id=None):
    if request.method == "POST":
        delete_cache()
        if "id" in request.POST:
            daytype_id = request.POST["id"]

            if "make_copy" in request.POST:
                daytype = get_object_or_404(DayType, id=daytype_id)
                blocks = daytype.blocks.all()
                daytype.pk = None
                daytype.name += " (Copy)"
                daytype.save()
                for blk in blocks:
                    daytype.blocks.add(blk)
                daytype.save()

                if "return_url" in request.POST:
                    return HttpResponse(reverse("schedule_daytype", args=[daytype.id]))

                return redirect("schedule_daytype", daytype.id)

            if "delete" in request.POST:
                daytype = get_object_or_404(DayType, id=daytype_id)
                name = "{}".format(daytype)
                daytype.delete()
                messages.success(request, "Deleted {}".format(name))
                return redirect("schedule_admin")

        if daytype_id:
            daytype = get_object_or_404(DayType, id=daytype_id)
            form = DayTypeForm(request.POST, instance=daytype)
        else:
            daytype = None
            form = DayTypeForm(request.POST)
        if form.is_valid():
            model = form.save()
            """Add blocks"""
            blocks = zip(
                request.POST.getlist("block_order"),
                request.POST.getlist("block_name"),
                [[int(j) if j else 0 for j in i.split(":")] if ":" in i else [9, 0] for i in request.POST.getlist("block_start")],
                [[int(j) if j else 0 for j in i.split(":")] if ":" in i else [10, 0] for i in request.POST.getlist("block_end")],
            )
            model.blocks.all().delete()
            for blk in blocks:
                start, _ = Time.objects.get_or_create(hour=blk[2][0], minute=blk[2][1])
                end, _ = Time.objects.get_or_create(hour=blk[3][0], minute=blk[3][1])
                bobj, _ = Block.objects.get_or_create(order=blk[0], name=blk[1], start=start, end=end)
                model.blocks.add(bobj)
            model.save()

            if "assign_date" in request.POST:
                assign_date = request.POST.get("assign_date")
                try:
                    dayobj = Day.objects.get(date=assign_date)
                except Day.DoesNotExist:
                    dayobj = Day.objects.create(date=assign_date, day_type=model)
                else:
                    dayobj.day_type = model
                    dayobj.save()
                messages.success(request, "{} is now a {}".format(dayobj.date, dayobj.day_type))

            messages.success(request, "Successfully {} Day Type.".format("modified" if daytype_id else "added"))
            return redirect("schedule_daytype", model.id)
        else:
            messages.error(request, "Error adding Day Type")
    elif daytype_id:
        daytype = get_object_or_404(DayType, id=daytype_id)
        form = DayTypeForm(instance=daytype)
    else:
        daytype = None
        form = DayTypeForm()

    context = {"form": form, "action": "add", "daytype": daytype}

    if "assign_date" in request.GET:
        context["assign_date"] = request.GET.get("assign_date")

    return render(request, "schedule/admin_daytype.html", context)
