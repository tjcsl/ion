import datetime

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render
from django.utils import timezone

from ..auth.decorators import deny_restricted
from ..schedule.models import Day
from .models import Route


@login_required
@deny_restricted
def home(request):
    now = timezone.localtime()
    if now.hour >= settings.BUS_PAGE_CHANGEOVER_HOUR:  # afternoon
        return afternoon(request, True)
    else:  # morning
        return morning(request, True)


@login_required
@deny_restricted
def morning(request, on_home=False):
    if not settings.ENABLE_BUS_APP:
        raise Http404("Bus app not enabled.")
    is_bus_admin = request.user.has_admin_permission("bus")
    routes = Route.objects.all()
    ctx = {
        "admin": is_bus_admin,
        "enable_bus_driver": settings.ENABLE_BUS_DRIVER,
        "bus_list": routes,
        "changeover_time": settings.BUS_PAGE_CHANGEOVER_HOUR,
        "on_home": on_home,
    }
    return render(request, "bus/morning.html", context=ctx)


@login_required
@deny_restricted
def afternoon(request, on_home=False):
    if not settings.ENABLE_BUS_APP:
        raise Http404("Bus app not enabled.")
    is_bus_admin = request.user.has_admin_permission("bus")

    now = timezone.localtime()
    day = Day.objects.today()
    if day is not None and day.end_time is not None:
        end_of_day = day.end_time.date_obj(now.date())
    else:
        end_of_day = datetime.datetime(now.year, now.month, now.day, settings.SCHOOL_END_HOUR, settings.SCHOOL_END_MINUTE)

    ctx = {
        "admin": is_bus_admin,
        "enable_bus_driver": settings.ENABLE_BUS_DRIVER,
        "changeover_time": settings.BUS_PAGE_CHANGEOVER_HOUR,
        "school_end_hour": end_of_day.hour,
        "school_end_time": end_of_day.minute,
        "on_home": on_home,
    }
    return render(request, "bus/home.html", context=ctx)
