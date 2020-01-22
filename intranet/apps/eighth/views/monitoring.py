from django.conf import settings
from django.db.models import Count, F
from django.shortcuts import render

from ..models import EighthBlock


def metrics_view(request):
    remote_addr = request.META["HTTP_X_REAL_IP"] if "HTTP_X_REAL_IP" in request.META else request.META.get("REMOTE_ADDR", "")
    is_admin = request.user.is_authenticated and not request.user.is_restricted and request.user.has_admin_permission("eighth")

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

    metrics = {"intranet_eighth_next_block_signups": num_next_block_signups, "intranet_eighth_next_block_signups_remaining": num_next_block_remaining}

    # How this works:
    # - We list all the blocks this year
    # - For each block, we find 1) the total number of users signed up and 2) the number of users signed up, removing duplicates
    # - We only look at blocks where the total is higher than the number without duplicates
    # - We subtract the number without duplicates from the total to find the number of duplicates
    for block_id, num_duplicates in (
        EighthBlock.objects.get_blocks_this_year()
        .annotate(
            total_signups=Count("eighthscheduledactivity__eighthsignup_set__user"),
            unique_signups=Count("eighthscheduledactivity__eighthsignup_set__user", distinct=True),
        )
        .filter(unique_signups__lt=F("total_signups"))
        .values_list("id", F("total_signups") - F("unique_signups"))
        .nocache()
    ):
        metrics['intranet_eighth_duplicate_signups{{block_id="{}"}}'.format(block_id)] = num_duplicates

    context = {"metrics": metrics}

    return render(request, "monitoring/prometheus-metrics.txt", context, content_type="text/plain")
