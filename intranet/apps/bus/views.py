from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import Http404
from django.shortcuts import render


@login_required
def home(request):
    if not settings.ENABLE_BUS_APP:
        raise Http404("Bus app not enabled.")
    is_bus_admin = request.user.has_admin_permission("bus")
    ctx = {'admin': is_bus_admin}
    return render(request, 'bus/home.html', context=ctx)
