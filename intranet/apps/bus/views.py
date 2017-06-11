from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def home(request):
    is_bus_admin = request.user.has_admin_permission("bus")
    ctx = {'admin': is_bus_admin}
    return render(request, 'bus/home.html', context=ctx)
