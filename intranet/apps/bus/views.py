from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Route


@login_required
def home(request):
    is_bus_admin = request.user.has_admin_permission("bus")
    arrived = Route.objects.filter(status="a")
    delayed = Route.objects.filter(status="d")
    on_time = Route.objects.filter(status="o")

    statuses = {
            "Arrived": {
                "buses": arrived,
                "empty": "No buses have arrived yet...",
                "order": 0
            },
            "On Time": {
                "buses": on_time,
                "empty": "No buses are on time...",
                "order": 1
            },
            "Delayed": {
                "buses": delayed,
                "empty": "No buses are delayed :)",
                "order": 2
            }
    }

    verbose_status = {
            'o': 'scheduled to arrive on time.',
            'a': 'already here!',
            'd': 'delayed.'
    }

    user_bus = Route.objects.get(user=request.user)
    print(user_bus.status, '================')
    ctx = {'admin': is_bus_admin,
            'statuses': sorted(statuses.items(), key=lambda k: (k[1]['order'])),
            'user_bus': user_bus,
            'user_bus_status': verbose_status[user_bus.status]}
    return render(request, 'bus/home.html', context=ctx)
