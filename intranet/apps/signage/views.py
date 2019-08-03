import logging

from django.conf import settings
from django.shortcuts import get_object_or_404, render

from ..schedule.views import schedule_context
from .models import Sign

logger = logging.getLogger(__name__)


def check_internal_ip(request):
    remote_addr = (request.META["HTTP_X_FORWARDED_FOR"] if "HTTP_X_FORWARDED_FOR" in request.META else request.META.get("REMOTE_ADDR", ""))
    if not request.user.is_authenticated and remote_addr not in settings.INTERNAL_IPS:
        return render(request, "error/403.html", {"reason": "You are not authorized to view this page."}, status=403)

    return None


def signage_display(request, display_id):
    check_ip = check_internal_ip(request)
    if check_ip:
        return check_ip
    sign = get_object_or_404(Sign, display=display_id)
    context = schedule_context(request)
    context["sign"] = sign
    context["page_args"] = (sign, request)
    return render(request, "signage/base.html", context)
