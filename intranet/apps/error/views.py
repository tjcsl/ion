from django.conf import settings
from django.shortcuts import render


def handle_404_view(request, exception):
    # TODO: Actually render the exception?
    del exception
    return render(request, "error/404.html", status=404)


def handle_500_view(request):
    return render(request, "error/500.html", {"public_dsn": settings.SENTRY_PUBLIC_DSN}, status=500)


def handle_503_view(request):
    # maintenance mode
    return render(request, "error/503.html", status=503)


def handle_csrf_view(request, reason):
    # CSRF failure view
    return render(request, "error/csrf.html", {"reason": reason}, status=403)
