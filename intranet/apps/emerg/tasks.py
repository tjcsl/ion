import requests
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.cache import cache
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from .views import update_emerg_cache

logger = get_task_logger(__name__)


@shared_task
def update_emerg_cache_task() -> None:
    logger.debug("Updating FCPS emergency info")
    update_emerg_cache(custom_logger=logger)


@shared_task
def update_csl_status_task() -> None:
    """Updates the cached status of the tjCSL status page.

    Returns:
        Nothing
    """
    logger.debug("Updating CSL Status")
    session = requests.Session()
    adapter = HTTPAdapter(
        max_retries=Retry(
            total=settings.CSL_STATUS_PAGE_MAX_RETRIES, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504], allowed_methods=["GET"]
        )
    )
    session.mount("https://", adapter)

    try:
        response = session.get(settings.CSL_STATUS_PAGE, timeout=settings.CSL_STATUS_PAGE_TIMEOUT)
        response.raise_for_status()
        status = response.json()["data"]["attributes"]["aggregate_state"]
    except Exception as ex:
        status = "error"
        logger.error(f"Could not fetch status page or incorrect status page JSON format: {ex}")

    cache.set("emerg:csl_status", status, settings.CACHE_AGE["csl_status"])
