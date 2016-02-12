# -*- coding: utf-8 -*-

import datetime
import logging
from .views import schedule_context

logger = logging.getLogger(__name__)

def chrome_getdata_check(request):
    ctx = schedule_context(request)
    blocks = ctx["sched_ctx"]["blocks"]
    point, block = at_period_point(blocks)
    logger.debug((point, block))
    if point == 1:
        return {
            "title": "{} has started".format(block.name),
            "text": "{}".format(block)
        }
    elif point == 2:
        return {
            "title": "{} has ended".format(block.name),
            "text": "{}".format(block)
        }
    else:
        return None


def at_period_point(blocks):
    now = datetime.datetime.now()
    now = datetime.datetime(now.year, now.month, now.day, now.hour, now.minute)
    for b in blocks:
        logger.debug(now, b.start.date_obj(now))
        if now == b.start.date_obj(now):
            return (1, b)
        elif now == b.end.date_obj(now):
            return (2, b)
    return (0, None)
