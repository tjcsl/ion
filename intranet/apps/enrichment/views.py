import logging
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta

from django import http
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from ...utils.html import safe_html
from ..auth.decorators import deny_restricted
from .forms import EnrichmentActivityForm
from .models import EnrichmentActivity

logger = logging.getLogger(__name__)


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


def enrichment_context(request, date=None):
    local_time = timezone.localtime()

    if date is None:
        date = local_time

    date_today = date.replace(hour=0, minute=0, second=0, microsecond=0)

    if timezone.is_naive(date_today):
        date_today = timezone.make_aware(date_today)

    date_tomorrow = date_today + timedelta(days=1)
    viewable_enrichments = EnrichmentActivity.objects.visible_to_user(request.user)
    enrichments = viewable_enrichments.filter(time__range=[date_today, date_tomorrow])

    display = True
    has_enrichments = True

    if not enrichments:
        has_enrichments = False

    if not enrichments and not is_weekday(date):  # don't display if there are no enrichments and it is a weekend
        display = False

    data = {
        "enrichment_ctx": {
            "date": date,
            "date_today": date_format(date_today),
            "enrichments": enrichments,
            "display": display,
            "has_enrichments": has_enrichments,
        }
    }
    return data


def week_data(request, date=None):
    if date:
        start_date = date
    elif "date" in request.GET:
        start_date = decode_date(request.GET["date"])
    else:
        start_date = enrichment_context(request)["enrichment_ctx"]["date"]

    delta = start_date.isoweekday() - 1
    start_date -= timedelta(days=delta)

    days = []
    for i in range(7):
        new_date = start_date + timedelta(days=i)
        days.append(enrichment_context(request, date=new_date))

    next_week = date_format(start_date + timedelta(days=7))
    last_week = date_format(start_date - timedelta(days=7))
    today = date_format(timezone.localtime())

    data = {
        "days": days,
        "next_week": next_week,
        "last_week": last_week,
        "today": today,
    }
    return data


def month_data(request):
    if "date" in request.GET:
        start_date = decode_date(request.GET["date"])
    else:
        start_date = timezone.localtime()

    delta = (int(date_format(start_date)[8:]) // 7) * 7
    start_date -= timedelta(days=delta)

    week1 = week_data(request, start_date)
    week2 = week_data(request, date=decode_date(week1["next_week"]))
    week3 = week_data(request, date=decode_date(week2["next_week"]))
    week4 = week_data(request, date=decode_date(week3["next_week"]))
    week5 = week_data(request, date=decode_date(week4["next_week"]))

    month = start_date.strftime("%B")
    one_month = relativedelta(months=1)
    next_month = date_format(start_date + one_month)
    last_month = date_format(start_date - one_month)

    data = {"weeks": [week1, week2, week3, week4, week5], "next_month": next_month, "last_month": last_month, "current_month": month}
    return data


@login_required
@deny_restricted
def enrichment_view(request):
    """Enrichment homepage.

    Shows a list of enrichments occurring in the next week, month, and
    future.
    """

    is_enrichment_admin = request.user.has_admin_permission("enrichment")

    show_all = False
    if is_enrichment_admin:
        if "show_all" in request.GET:
            show_all = True
            viewable_enrichments = EnrichmentActivity.objects.all()
        else:
            viewable_enrichments = EnrichmentActivity.objects.all().this_year()
    else:
        viewable_enrichments = EnrichmentActivity.objects.visible_to_user(request.user).this_year()

    classic = "classic" in request.GET

    # get date objects for week and month
    today = timezone.localtime()
    delta = today - timezone.timedelta(days=today.weekday())
    this_week = (delta, delta + timezone.timedelta(days=7))
    this_month = (this_week[1], this_week[1] + timezone.timedelta(days=31))

    enrichments_categories = [
        {"title": "This week", "enrichments": viewable_enrichments.filter(time__gte=this_week[0], time__lt=this_week[1])},
        {"title": "This month", "enrichments": viewable_enrichments.filter(time__gte=this_month[0], time__lt=this_month[1])},
    ]

    week_and_month = viewable_enrichments.filter(time__gte=this_week[0], time__lt=this_month[1])
    if not show_all and not classic:
        enrichments_categories.append(
            {
                "title": "Week and month",
                "enrichments": week_and_month,
            }
        )

    if is_enrichment_admin:
        past_enrichments = viewable_enrichments.filter(time__lt=this_week[0])
        future_enrichments = viewable_enrichments.filter(time__gte=this_month[1])

        if show_all:
            enrichments_categories.append({"title": "Future", "enrichments": future_enrichments})
            enrichments_categories.append({"title": "Past", "enrichments": past_enrichments})

    num_enrichments = viewable_enrichments.filter(time__gte=this_week[0], time__lt=this_month[1]).count()

    context = {
        "enrichments": enrichments_categories,
        "authorized_enrichments": {e.id for e in week_and_month if e.user_can_signup(request.user)},
        "blacklisted_enrichments": {e.id for e in week_and_month if e.user_is_blacklisted(request.user)},
        "num_enrichments": num_enrichments,
        "is_enrichment_admin": is_enrichment_admin,
        "show_attend": True,
        "show_icon": False,
        "show_all": show_all,
        "classic": classic,
        "today": date_format(today),
    }
    context["week_data"] = week_data(request)
    context["month_data"] = month_data(request)

    if "view" in request.GET and request.GET["view"] == "month":
        context["view"] = "month"
    else:
        context["view"] = "week"

    return render(request, "enrichment/home.html", context)


@login_required
@deny_restricted
def enrichment_signup_view(request, enrichment_id):
    if request.method == "POST":
        enrichment = get_object_or_404(EnrichmentActivity, id=enrichment_id)

        if enrichment.happened:  # and request.POST.get("attending") == "true":
            messages.error(request, "Signups are locked for this enrichment activity.")
            return redirect("enrichment")

        if not enrichment.user_can_signup(request.user):
            messages.error(request, "You do not have permission to sign up for this enrichment activity.")
            return redirect("enrichment")

        if enrichment.presign:
            too_early_to_signup = enrichment.is_too_early_to_signup
            if too_early_to_signup[0]:
                messages.error(
                    request,
                    "You may not sign up for this enrichment activity until " f"{too_early_to_signup[1].strftime('%A, %B %-d at %-I:%M %p')}.",
                )
                return redirect("enrichment")

        if request.user not in enrichment.attending.all() and enrichment.attending.count() >= enrichment.capacity:
            messages.error(request, "The capacity for this enrichment activity has been reached. You may not sign up for it at this time.")
            return redirect("enrichment")

        enrichment_date = enrichment.time.astimezone(timezone.get_default_timezone()).strftime("%A, %B %-d at %-I:%M %p")
        if request.POST.get("attending") == "true":
            enrichment.attending.add(request.user)
            messages.success(request, f"Signed up for {enrichment.title} on {enrichment_date}.")
        else:
            enrichment.attending.remove(request.user)
            messages.warning(request, f"Removed signup for {enrichment.title} on {enrichment_date}.")
    return redirect("enrichment")


@login_required
@deny_restricted
def enrichment_roster_view(request, enrichment_id):
    """Show the enrichment activity roster.

    Args:
        enrichment_id (int): the enrichment activity id
    """
    is_enrichment_admin = request.user.has_admin_permission("enrichment")

    enrichment = get_object_or_404(EnrichmentActivity, id=enrichment_id)
    enrichment_is_today = (
        enrichment.time.astimezone(timezone.get_default_timezone()).date() == timezone.now().astimezone(timezone.get_default_timezone()).date()
    )

    context = {
        "enrichment": enrichment,
        "authorized_enrichments": {enrichment.id if enrichment.user_can_signup(request.user) else None},
        "blacklisted_enrichments": {enrichment.id if enrichment.user_is_blacklisted(request.user) else None},
        "enrichment_time": enrichment.time.astimezone(timezone.get_default_timezone()),
        "enrichment_is_today": enrichment_is_today,
        "roster": enrichment.attending.all().order_by("first_name", "last_name"),
        "is_enrichment_admin": is_enrichment_admin,
        "today": timezone.now().date(),
    }
    return render(request, "enrichment/roster.html", context)


@login_required
@deny_restricted
def add_enrichment_view(request):
    """Add enrichment activity page."""

    is_enrichment_admin = request.user.has_admin_permission("enrichment")

    if not is_enrichment_admin:
        raise http.Http404

    if request.method == "POST":
        form = EnrichmentActivityForm(data=request.POST)
        if form.is_valid():
            obj = form.save()
            obj.user = request.user
            # SAFE HTML
            obj.description = safe_html(obj.description)

            logger.info("Admin %s added enrichment activity: %s (%s)", request.user, obj, obj.id)
            obj.save()

            return redirect("enrichment")
        else:
            messages.error(request, "Error adding enrichment activity.")
    else:
        form = EnrichmentActivityForm()
    context = {"form": form, "action": "add", "action_title": "Add", "is_enrichment_admin": is_enrichment_admin}
    return render(request, "enrichment/add_modify.html", context)


@login_required
@deny_restricted
def modify_enrichment_view(request, enrichment_id):
    """Modify enrichment activity page.

    Args:
        enrichment_id (int): enrichment activity id
    """

    enrichment = get_object_or_404(EnrichmentActivity, id=enrichment_id)
    is_enrichment_admin = request.user.has_admin_permission("enrichment")

    if not is_enrichment_admin:
        raise http.Http404

    if request.method == "POST":
        form = EnrichmentActivityForm(data=request.POST, instance=enrichment)
        if form.is_valid():
            obj = form.save()
            # SAFE HTML
            obj.description = safe_html(obj.description)
            obj.save()
            messages.success(request, "Successfully modified enrichment activity.")
            logger.info("Admin %s modified enrichment activity: %s (%s)", request.user, obj, obj.id)
        else:
            messages.error(request, "Error modifying enrichment activity.")
        return redirect("enrichment")
    else:
        form = EnrichmentActivityForm(instance=enrichment)
    context = {"form": form, "action": "modify", "action_title": "Modify", "enrichment": enrichment, "is_enrichment_admin": is_enrichment_admin}
    return render(request, "enrichment/add_modify.html", context)


@login_required
@deny_restricted
def delete_enrichment_view(request, enrichment_id):
    """Delete enrichment activity page.

    Args:
        enrichment_id: enrichment activity id
    """
    enrichment = get_object_or_404(EnrichmentActivity, id=enrichment_id)
    if not request.user.has_admin_permission("enrichment"):
        raise http.Http404

    if request.method == "POST":
        enrichment_title = enrichment.title
        enrichment_time = enrichment.time
        enrichment.delete()
        messages.warning(request, f'Deleted enrichment activity: "{enrichment_title}" scheduled on {enrichment_time.date()}')
        logger.info("Admin %s deleted enrichment activity: %s (%s)", request.user, enrichment, enrichment.id)
        return redirect("enrichment")
    else:
        return render(request, "enrichment/delete.html", {"enrichment": enrichment, "action": "delete"})
