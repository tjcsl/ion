import logging
import time

import requests
from bs4 import BeautifulSoup, CData

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


def check_emerg():
    """Fetch from FCPS' emergency announcement page.

    URL defined in settings.FCPS_EMERGENCY_PAGE

    Request timeout defined in settings.FCPS_EMERGENCY_TIMEOUT

    """
    status = True
    message = None
    if settings.EMERGENCY_MESSAGE:
        return True, settings.EMERGENCY_MESSAGE
    if not settings.FCPS_EMERGENCY_PAGE:
        return None, None

    timeout = settings.FCPS_EMERGENCY_TIMEOUT

    r = requests.get("{}?{}".format(settings.FCPS_EMERGENCY_PAGE, int(time.time() // 60)), timeout=timeout)
    res = r.text
    if not res:
        status = False

    # Keep this list up to date with whatever wording FCPS decides to use each time...
    bad_strings = [
        "There are no emergency announcements at this time", "There are no emergency messages at this time",
        "There are no emeregency annoncements at this time", "There are no major announcements at this time.",
        "There are no major emergency announcements at this time.", "There are no emergencies at this time."
    ]
    for b in bad_strings:
        if b in res:
            status = False
            break

    # emerg_split = '<p><a href="https://youtu.be/jo_8QFIEf64'
    # message = res.split(emerg_split)[0]
    soup = BeautifulSoup(res, "html.parser")
    if soup.title:
        title = soup.title.text
        body = ""
        for cd in soup.findAll(text=True):
            if isinstance(cd, CData):
                body += cd
        message = "<h3>{}: </h3>{}".format(title, body)
        message = message.strip()
    else:
        status = False

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
    key = "emerg:{}".format(timezone.localdate())
    cached = cache.get(key)
    if cached:
        logger.debug("Returning emergency info from cache")
        return cached
    else:
        result = get_emerg_result()
        cache.set(key, result, timeout=settings.CACHE_AGE["emerg"])
        return result
