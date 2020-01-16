from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render

from ..auth.decorators import deny_restricted


@login_required
@deny_restricted
def home(request):
    if not settings.ENABLE_BUS_APP:
        raise Http404("Bus app not enabled.")
    is_bus_admin = request.user.has_admin_permission("bus")
    ctx = {"admin": is_bus_admin, "enable_bus_driver": settings.ENABLE_BUS_DRIVER}
    return render(request, "bus/home.html", context=ctx)
