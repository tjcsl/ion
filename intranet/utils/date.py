import datetime

from django.conf import settings
from django.utils import timezone


def is_current_year(date):
    start_date, end_date = get_date_range_this_year()
    return start_date <= date <= end_date


def get_date_range_this_year(now=None):
    """Return the starting and ending date of the current school year."""
    if now is None:
        now = datetime.datetime.now().date()
    if now.month <= settings.YEAR_TURNOVER_MONTH:
        date_start = datetime.datetime(now.year - 1, settings.YEAR_TURNOVER_MONTH + 1, 1)
        date_end = datetime.datetime(now.year, settings.YEAR_TURNOVER_MONTH, 1)
    else:
        date_start = datetime.datetime(now.year, settings.YEAR_TURNOVER_MONTH + 1, 1)
        date_end = datetime.datetime(now.year + 1, settings.YEAR_TURNOVER_MONTH, 1)
    return timezone.make_aware(date_start), timezone.make_aware(date_end)
