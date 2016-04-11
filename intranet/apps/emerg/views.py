# -*- coding: utf-8 -*-

import datetime
import logging
import time

from django.conf import settings
from django.core.cache import cache

import requests

logger = logging.getLogger(__name__)


def check_emerg():
    """Fetch from FCPS' emergency announcement page.

    URL defined in settings.FCPS_EMERGENCY_PAGE
    Request timeout defined in settings.FCPS_EMERGENCY_TIMEOUT
    """
    status = True
    message = None
    if not settings.FCPS_EMERGENCY_PAGE:
        return None, None

    timeout = settings.FCPS_EMERGENCY_TIMEOUT

    r = requests.get("{}?{}".format(settings.FCPS_EMERGENCY_PAGE, int(time.time())), timeout=timeout)
    res = r.text
    if not res or len(res) < 1:
        status = False

    # Keep this list up to date with whatever wording FCPS decides to use each time...
    bad_strings = ["There are no emergency announcements at this time", "There are no emergency messages at this time",
                   "There are no emeregency annoncements at this time", "There are no major announcements at this time.",
                   "There are no major emergency announcements at this time.",
                   "There are no emergencies at this time."]
    for b in bad_strings:
        if b in res:
            status = False
            break

    emerg_split = '<p><a href="https://youtu.be/jo_8QFIEf64'
    message = res.split(emerg_split)[0]

    message = message.strip()

    return status, message


def get_emerg_result():
    """Run the fetch command from FCPS."""
    logger.debug("Fetching emergency info from FCPS")
    status, message = check_emerg()
    return {"status": status, "message": message}


def get_emerg():
    """Get the cached FCPS emergency page, or check it again.

    Timeout defined in settings.CACHE_AGE["emerg"]
    """
    key = "emerg:{}".format(datetime.datetime.now().date())
    cached = cache.get(key)
    if cached:
        logger.debug("Returning emergency info from cache")
        return cached
    else:
        result = get_emerg_result()
        cache.set(key, result, timeout=settings.CACHE_AGE["emerg"])
        return result
