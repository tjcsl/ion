# -*- coding: utf-8 -*-
import datetime


def is_current_year(date):
    start_date, end_date = get_date_range_this_year()
    return start_date <= date <= end_date


def get_date_range_this_year():
    """Return the starting and ending date of the current school year."""
    now = datetime.datetime.now().date()
    if now.month < 9:
        date_start = datetime.date(now.year - 1, 9, 1)
        date_end = datetime.date(now.year, 7, 1)
    else:
        date_start = datetime.date(now.year, 9, 1)
        date_end = datetime.date(now.year + 1, 7, 1)
    return date_start, date_end
