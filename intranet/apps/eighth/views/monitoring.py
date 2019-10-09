from django.conf import settings
from django.shortcuts import render

from ..models import EighthBlock


def metrics_view(request):
    remote_addr = request.META["HTTP_X_FORWARDED_FOR"] if "HTTP_X_FORWARDED_FOR" in request.META else request.META.get("REMOTE_ADDR", "")
    is_admin = request.user.is_authenticated and request.user.has_admin_permission("eighth")

    # If they're not from an IP on the white list and they're not an eighth admin, deny access
    if remote_addr not in settings.ALLOWED_METRIC_SCRAPE_IPS and not is_admin:
        return render(request, "error/403.html", {"reason": "You are not authorized to view this page."}, status=403)

    next_block = EighthBlock.objects.get_first_upcoming_block()
    if next_block is not None:
        num_next_block_signups = next_block.num_signups()
        num_next_block_remaining = next_block.num_no_signups()
    else:
        num_next_block_signups = 0
        num_next_block_remaining = 0

    context = {
        "metrics": {
            "intranet_eighth_next_block_signups": num_next_block_signups,
            "intranet_eighth_next_block_signups_remaining": num_next_block_remaining,
        },
    }

    return render(request, "eighth/prometheus-metrics.txt", context, content_type="text/plain")
