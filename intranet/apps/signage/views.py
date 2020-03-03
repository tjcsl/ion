import datetime
import logging

from django import http
from django.conf import settings
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from ...utils.serialization import safe_json
from ..eighth.models import EighthBlock
from ..eighth.serializers import EighthBlockDetailSerializer
from ..schedule.models import Day
from ..schedule.views import schedule_context
from ..users.models import User
from .models import Sign

logger = logging.getLogger(__name__)


def check_internal_ip(request):
    remote_addr = request.META["HTTP_X_REAL_IP"] if "HTTP_X_REAL_IP" in request.META else request.META.get("REMOTE_ADDR", "")
    if (not request.user.is_authenticated or request.user.is_restricted) and remote_addr not in settings.INTERNAL_IPS:
        return render(request, "error/403.html", {"reason": "You are not authorized to view this page."}, status=403)

    return None


def signage_display(request, display_id):
    check_ip = check_internal_ip(request)
    if check_ip:
        return check_ip
    sign = get_object_or_404(Sign, display=display_id)

    now = timezone.localtime()
    day = Day.objects.today()
    if day is not None and day.end_time is not None:
        end_of_day = day.end_time.date_obj(now.date())
    else:
        end_of_day = datetime.datetime(now.year, now.month, now.day, 16, 0)

    context = schedule_context(request)
    context["sign"] = sign
    context["page_args"] = (sign, request)
    context["end_switch_page_time"] = end_of_day - datetime.timedelta(minutes=sign.day_end_switch_minutes)
    return render(request, "signage/base.html", context)


def eighth(request):
    """Displays the eighth period signage page. This cannot be a regular signage page because it needs to reload
    in order to switch blocks or update information.."""
    internal_ip = check_internal_ip(request)
    if internal_ip:
        return internal_ip

    block_id = request.GET.get("block_id")
    if block_id is None:
        block = EighthBlock.objects.get_first_upcoming_block()
        if block is None:
            raise http.Http404
    else:
        block = get_object_or_404(EighthBlock.objects.prefetch_related("eighthscheduledactivity_set"), id=block_id)

    # If block_increment is specified, the eighth period block that is <block_increment> blocks ahead of the current
    # block (or the block specified with block_id) will be displayed. This is used in the template to skip to A/B
    # blocks.
    try:
        block_increment = int(request.GET.get("block_increment", 0))
    except ValueError:
        block_increment = 0

    if block_increment > 0:
        next_blocks = block.next_blocks()
        if next_blocks.count() >= block_increment:
            block = next_blocks[block_increment - 1]
    elif block_increment < 0:
        index = -block_increment - 1
        prev_blocks = block.previous_blocks()
        if prev_blocks.count() > index:
            block = prev_blocks[index]

    user = User.get_signage_user()

    serializer_context = {"request": request, "user": user}
    block_info = EighthBlockDetailSerializer(block, context=serializer_context).data
    try:
        reload_mins = float(request.GET.get("reload_mins", 5))
    except ValueError:
        reload_mins = 5

    touch_signage = not request.GET.get("no_touch")

    try:
        next_block = block.next_blocks(1)[0]
        if next_block.date != block.date:
            next_block = None
    except IndexError:
        next_block = None

    try:
        prev_block = block.previous_blocks(1)[0]
        if prev_block.date != block.date:
            prev_block = None
    except IndexError:
        prev_block = None

    use_scroll = not touch_signage and bool(request.GET.get("scroll"))

    context = {
        "user": user,
        "block_info": block_info,
        "activities_list": safe_json(block_info["activities"]),
        "active_block": block,
        "active_block_current_signup": None,
        "no_title": bool(request.GET.get("no_title")),
        "no_detail": bool(request.GET.get("no_detail")),
        "no_rooms": bool(request.GET.get("no_rooms")),
        "use_scroll": use_scroll,
        "do_reload": not bool(request.GET.get("no_reload")),
        "preload_background": True,
        "reload_mins": reload_mins,
        "no_user_display": True,
        "no_fav": True,
        "touch_signage": touch_signage,
        "next_block": next_block,
        "prev_block": prev_block,
        "signage": True,
    }

    return render(request, "signage/pages/eighth.html", context)


def prometheus_metrics(request):
    """Prometheus metrics for signage displays. Currently just whether or not they are online."""

    remote_addr = request.META["HTTP_X_REAL_IP"] if "HTTP_X_REAL_IP" in request.META else request.META.get("REMOTE_ADDR", "")
    is_admin = request.user.is_authenticated and not request.user.is_restricted and request.user.is_superuser

    # If they're not from an IP on the white list and they're not an admin, deny access
    if remote_addr not in settings.ALLOWED_METRIC_SCRAPE_IPS and not is_admin:
        return render(request, "error/403.html", {"reason": "You are not authorized to view this page."}, status=403)

    metrics = {"intranet_signage_num_signs_online": Sign.objects.filter_online().count()}

    for sign in Sign.objects.all():
        metrics['intranet_signage_sign_is_online{{display="{}"}}'.format(sign.display)] = int(not sign.is_offline)

    context = {"metrics": metrics}

    return render(request, "monitoring/prometheus-metrics.txt", context, content_type="text/plain")
