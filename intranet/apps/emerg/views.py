import logging
import time
from typing import Tuple

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from ...utils.html import get_domain_name, safe_fcps_emerg_html

logger = logging.getLogger(__name__)


def check_emerg():
    """Fetch from FCPS emergency announcement pages.

    URLs defined in settings.FCPS_EMERGENCY_PAGE

    Request timeout defined in settings.FCPS_EMERGENCY_TIMEOUT

    """
    fcps_page = settings.FCPS_EMERGENCY_PAGE
    announcements = []

    if settings.EMERGENCY_MESSAGE:
        return True, settings.EMERGENCY_MESSAGE
    if not fcps_page:
        return None, None

    timeout = settings.EMERGENCY_TIMEOUT

    try:
        r = requests.get(f"{fcps_page}?{int(time.time() // 60)}", timeout=timeout)
    except requests.exceptions.Timeout:
        return False, None

    res = r.text

    # Keep this list up to date with whatever wording FCPS decides to use each time...
    bad_strings = [
        "There are no emergency announcements at this time",
        "There are no emergency messages at this time",
        "There are no emeregency annoncements at this time",  # codespell: ignore
        "There are no major announcements at this time.",
        "There are no major emergency announcements at this time.",
        "There are no emergencies at this time.",
        "Site under maintenance",  # We don't want to get people's attention like this just to tell them that fcps.edu is under maintenance
        "502 Bad Gateway",
    ]

    status = True
    for b in bad_strings:
        if b in res:
            status = False
            break

    soup = BeautifulSoup(res, "xml")
    if soup.title and status:
        title = soup.title.text
        body = soup.find("content").text

        title = safe_fcps_emerg_html(title, fcps_page)
        body = safe_fcps_emerg_html(body, fcps_page)

        announcements.append({"title": f"<a target='_blank' href=\"{get_domain_name(fcps_page)}\">{title}</a>", "body": body})

    message = "".join(
        [
            f"<h3><i class='fas fa-exclamation-triangle'></i>&nbsp; {announcement['title']}</h3><hr />{announcement['body']}\n"
            for announcement in announcements
        ]
    )

    return status, message


def get_emerg_result(*, custom_logger=None):
    """Run the fetch command from FCPS."""
    if custom_logger is None:
        custom_logger = logger

    status, message = check_emerg()
    custom_logger.debug("Fetched emergency info from FCPS")
    return {"status": status, "message": message}


def get_emerg():
    """Get the cached FCPS emergency page, or check it again.

    Timeout defined in settings.CACHE_AGE["emerg"]

    """
    key = f"emerg:{timezone.localdate()}"
    cached = cache.get(key)
    if cached:
        return cached
    else:
        # We have a Celery task updating the cache periodically, so this normally won't run.
        # However, if Celery stops working, we still want it to update, so we fall back on
        # updating it here.
        result = get_emerg_result()
        cache.set(key, result, timeout=settings.CACHE_AGE["emerg"])
        return result


def update_emerg_cache(*, custom_logger=None) -> None:
    """Updates the cached contents of FCPS emergency page.

    This forces a cache update, regardless of whether or not the cache has
    expired. However, it does set the cache entry to expire in
    ``settings.CACHE_AGE["emerg"]`` seconds.

    Args:
        custom_logger: A custom ``logging.Logger`` instance to use for log
            messages relating to the cache update.

    """
    key = f"emerg:{timezone.localdate()}"
    result = get_emerg_result(custom_logger=custom_logger)
    cache.set(key, result, timeout=settings.CACHE_AGE["emerg"])


def get_csl_status() -> Tuple[str, bool]:
    """Get the cached status of the TJCSL status page.

    Returns:
        Tuple with a string consisting of the aggregate status
        of the TJ computer systems lab and a bool indicating whether
        the status cache was updated

        The string of the tuple will be one of the following: "error" (parse error), "operational", "downtime", "degraded", "maintenance"
    """

    status = cache.get("emerg:csl_status")
    updated = False

    if not status:
        response = requests.get(settings.CSL_STATUS_PAGE)
        if response.status_code != 200:
            status = "error"
            logger.error("Could not fetch status page")

        else:
            try:
                status = response.json()["data"]["attributes"]["aggregate_state"]
                updated = True
            except KeyError as e:
                status = "error"
                logger.error("Unexpected status page JSON format. %s", e)

        cache.set("emerg:csl_status", status, settings.CACHE_AGE["csl_status"])

    return status, updated
