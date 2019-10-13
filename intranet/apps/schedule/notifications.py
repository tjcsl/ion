import logging

from django.utils import timezone

from .views import schedule_context

logger = logging.getLogger(__name__)


def chrome_getdata_check(request):
    return period_start_end_data(request)


def period_start_end_data(request):
    ctx = schedule_context(request, use_cache=False, show_tomorrow=False)
    blocks = ctx["sched_ctx"]["blocks"]
    point, block = at_period_point(blocks)
    if point == 1:
        return {"title": "{} has started".format(block.name), "text": "{}".format(block)}
    elif point == 2:
        return {"title": "{} has ended".format(block.name), "text": "{}".format(block)}
    else:
        return None


def at_period_point(blocks):
    now = timezone.now()
    now = now.replace(second=0, microsecond=0)
    for b in blocks:
        if now == b.start.date_obj(now):
            return (1, b)
        elif now == b.end.date_obj(now):
            return (2, b)
    return (0, None)
