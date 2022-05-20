import json
import logging
import time

import requests
from bs4 import BeautifulSoup, CData

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from ...utils.html import safe_fcps_emerg_html

logger = logging.getLogger(__name__)


def check_emerg():
    """Fetch from FCPS' and CSL emergency announcement page.

    URL defined in settings.FCPS_EMERGENCY_PAGE

    Request timeout defined in settings.FCPS_EMERGENCY_TIMEOUT

    """
    announcements = []
    if settings.EMERGENCY_MESSAGE:
        return True, settings.EMERGENCY_MESSAGE
    if not settings.FCPS_EMERGENCY_PAGE or not settings.CSL_STATUS_PAGE:
        return None, None

    timeout = settings.EMERGENCY_TIMEOUT

    try:
        r = requests.get("{}?{}".format(settings.FCPS_EMERGENCY_PAGE, int(time.time() // 60)), timeout=timeout)
    except requests.exceptions.Timeout:
        return False, None

    res = r.text

    # Keep this list up to date with whatever wording FCPS decides to use each time...
    bad_strings = [
        "There are no emergency announcements at this time",
        "There are no emergency messages at this time",
        "There are no emeregency annoncements at this time",
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
    if soup.title and status is True:
        title = soup.title.text
        body = ""
        for cd in soup.findAll(text=True):
            if isinstance(cd, CData):
                body += cd

        title = safe_fcps_emerg_html(title, settings.FCPS_EMERGENCY_PAGE)
        body = safe_fcps_emerg_html(body, settings.FCPS_EMERGENCY_PAGE)

        announcements.append({"title": title, "body": body})

    try:
        r = requests.get(settings.CSL_STATUS_PAGE, timeout=timeout)
    except requests.exceptions.Timeout:
        pass

    try:
        csl_status = json.loads(r.text)
    except json.decoder.JSONDecodeError:
        return False, None

    for system in csl_status['systems']:
        if system['status'] != 'ok':
            status = True
            issues = system['unresolvedIssues']
            for issue in issues:
                desc = requests.get(issue['permalink']).text
                soup = BeautifulSoup(desc, "html.parser")
                desc = soup.find_all('p')[1].text
                a = {"title": issue['title'], "body": desc}
                if a not in announcements and issue['severity'] != 'notice':
                    announcements.append(a)

    message = ''.join([f"<h3>{announcement['title']}: </h3>{announcement['body']}\n" for announcement in announcements])

    return status, message


def get_emerg_result(*, custom_logger=None):
    """Run the fetch command from FCPS."""
    if custom_logger is None:
        custom_logger = logger

    status, message = check_emerg()
    custom_logger.debug("Fetched emergency info from FCPS and CSL status")
    return {"status": status, "message": message}


def get_emerg():
    """Get the cached FCPS emergency page and CSL status page, or check it again.

    Timeout defined in settings.CACHE_AGE["emerg"]

    """
    key = "emerg:{}".format(timezone.localdate())
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
    key = "emerg:{}".format(timezone.localdate())
    result = get_emerg_result(custom_logger=custom_logger)
    cache.set(key, result, timeout=settings.CACHE_AGE["emerg"])
