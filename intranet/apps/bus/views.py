from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render
from django.utils import timezone

from ..auth.decorators import deny_restricted
from .models import Route


@login_required
@deny_restricted
def home(request):
    if not settings.ENABLE_BUS_APP:
        raise Http404("Bus app not enabled.")
    is_bus_admin = request.user.has_admin_permission("bus")
    now = timezone.localtime()
    if now.hour > 12:  # afternoon bus page,
        is_bus_admin = request.user.has_admin_permission("bus")
        ctx = {"admin": is_bus_admin, "enable_bus_driver": settings.ENABLE_BUS_DRIVER}
        return render(request, "bus/home.html", context=ctx)
    else:  # morning bus page
        routes = Route.objects.all()
        ctx = {"admin": is_bus_admin, "enable_bus_driver": settings.ENABLE_BUS_DRIVER, "bus_list": routes}
        return render(request, "bus/morning.html", context=ctx)
