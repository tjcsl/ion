import json
import logging
import time

import requests
from bs4 import BeautifulSoup

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from ...utils.html import get_domain_name, safe_fcps_emerg_html

logger = logging.getLogger(__name__)


def check_emerg():
    """Fetch from FCPS and CSL emergency announcement pages.

    URLs defined in settings.FCPS_EMERGENCY_PAGE and settings.CSL_STATUS_PAGE

    Request timeout defined in settings.FCPS_EMERGENCY_TIMEOUT

    """
    fcps_page = settings.FCPS_EMERGENCY_PAGE
    csl_page = settings.CSL_STATUS_PAGE
    announcements = []

    if settings.EMERGENCY_MESSAGE:
        return True, settings.EMERGENCY_MESSAGE
    if not fcps_page or not csl_page:
        return None, None

    timeout = settings.EMERGENCY_TIMEOUT

    try:
        r = requests.get("{}?{}".format(fcps_page, int(time.time() // 60)), timeout=timeout)
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
    if soup.title and status:
        title = soup.title.text
        body = soup.find("content").text

        title = safe_fcps_emerg_html(title, fcps_page)
        body = safe_fcps_emerg_html(body, fcps_page)

        announcements.append({"title": f"<a target='_blank' href=\"{get_domain_name(fcps_page)}\">{title}</a>", "body": body})

    try:
        r = requests.get(csl_page, timeout=timeout)
    except requests.exceptions.Timeout:
        pass

    try:
        csl_status = json.loads(r.text)
    except json.decoder.JSONDecodeError:
        return False, None

    for system in csl_status["systems"]:
        if system["status"] != "ok":
            status = True
            issues = system["unresolvedIssues"]
            for issue in issues:
                desc = requests.get(issue["permalink"], timeout=timeout).text
                soup = BeautifulSoup(desc, "html.parser")

                text = soup.find_all(["p", "hr"])
                desc = text[2: len(text) - 5]
                a = {
                    "title": f"<a target='_blank' href=\"{get_domain_name(csl_page)}\">{issue['title']}</a>",
                    "body": "".join(d.prettify() for d in desc),
                }
                if a not in announcements and issue["severity"] != "notice":
                    announcements.append(a)

    # Not needed due to the filtering of "p" elements, but as a backup:
    bad_text = [
        '<p><strong class="bold">© tjCSL Status, 2022</strong>&nbsp; • &nbsp; <a href="#">Back to top</a></p>',
        "<p>We continuously monitor the status of our services and if there are any interruptions, a note will be posted here.</p>",
    ]

    message = "".join(
        [
            f"<h3><i class='fas fa-exclamation-triangle'></i>&nbsp; {announcement['title']}</h3><hr />{announcement['body']}\n"
            for announcement in announcements
            if announcement not in bad_text
        ]
    )

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
