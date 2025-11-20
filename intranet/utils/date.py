import calendar
import datetime

from django.conf import settings
from django.utils import timezone


def is_current_year(date):
    start_date, end_date = get_date_range_this_year()
    return start_date <= date <= end_date


def get_date_range_this_year(now=None):
    """Return the starting and ending date of the current school year."""
    if now is None:
        now = timezone.localdate()
    if now.month <= settings.YEAR_TURNOVER_MONTH:
        if settings.YEAR_TURNOVER_MONTH < 12:
            date_start = datetime.datetime(now.year - 1, settings.YEAR_TURNOVER_MONTH + 1, 1, 0, 0, 0)
        else:
            date_start = datetime.datetime(now.year, 1, 1, 0, 0, 0)
        date_end = datetime.datetime(
            now.year, settings.YEAR_TURNOVER_MONTH, calendar.monthrange(now.year, settings.YEAR_TURNOVER_MONTH)[1], 23, 59, 59
        )
    else:
        date_start = datetime.datetime(now.year, settings.YEAR_TURNOVER_MONTH + 1, 1, 0, 0, 0)
        date_end = datetime.datetime(now.year + 1, settings.YEAR_TURNOVER_MONTH, 1, 0, 0, 0)
    return timezone.make_aware(date_start), timezone.make_aware(date_end)


def get_senior_graduation_year(*, now=None):
    return get_date_range_this_year(now=now)[1].year


def get_senior_graduation_date():
    return settings.SENIOR_GRADUATION_DATE.replace(year=get_senior_graduation_year())
