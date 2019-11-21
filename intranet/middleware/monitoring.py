from django.conf import settings
from django.shortcuts import render


class PrometheusAccessMiddleware:
    """
    Restricts access to Django Prometheus metrics to ALLOWED_METRIC_IPS and superusers.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # We would like to be able to just check request.resolver_match.app_name. Unfortunately, URL resolving has not taken place yet, so we can't.
        if request.path == "/prometheus" or request.path.startswith("/prometheus/"):
            remote_addr = request.META["HTTP_X_REAL_IP"] if "HTTP_X_REAL_IP" in request.META else request.META.get("REMOTE_ADDR", "")
            is_superuser = request.user.is_authenticated and request.user.is_superuser

            # If they're not from an IP on the white list and they're not a superuser, deny access
            if remote_addr not in settings.ALLOWED_METRIC_SCRAPE_IPS and not is_superuser:
                return render(request, "error/403.html", {"reason": "You are not authorized to view this page."}, status=403)

        return self.get_response(request)
