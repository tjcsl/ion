# -*- coding: utf-8 -*-

import datetime
import logging
import time

from django.conf import settings
from django.core.cache import cache

import requests

logger = logging.getLogger(__name__)


def check_emerg():
    status = True
    message = None

    r = requests.get("{}?{}".format(settings.FCPS_EMERGENCY_PAGE, int(time.time())))
    res = r.text
    if not res or len(res) < 1:
        status = False

    bad_strings = ["There are no emergency announcements at this time", "There are no emergency messages at this time",
                   "There are no emeregency annoncements at this time", "There are no major announcements at this time.",
                   "There are no major emergency announcements at this time."]
    for b in bad_strings:
        if b in res:
            status = False
            break

    emerg_split = '<p><a href="https://youtu.be/jo_8QFIEf64'
    message = res.split(emerg_split)[0]

    message = message.strip()

    return status, message


def get_emerg_result():
    logger.debug("Fetching emergency info from FCPS")
    status, message = check_emerg()
    return {"status": status, "message": message}


def get_emerg():
    key = "emerg:{}".format(datetime.datetime.now().date())
    cached = cache.get(key)
    if cached:
        logger.debug("Returning emergency info from cache")
        return cached
    else:
        result = get_emerg_result()
        cache.set(key, result, timeout=settings.CACHE_AGE["emerg"])
        return result
