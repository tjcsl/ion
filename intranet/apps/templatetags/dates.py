# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from datetime import datetime
from django import template

register = template.Library()
logger = logging.getLogger(__name__)


@register.filter(expects_localtime=True)
def fuzzy_date(date):
    """Formats a :class:`datetime.datetime` object relative to the current time
    """

    date = date.replace(tzinfo=None)

    if date <= datetime.now():
        diff = datetime.now() - date

        seconds = diff.total_seconds()
        minutes = seconds // 60
        hours = minutes // 60

        if minutes <= 1:
            return "moments ago"
        elif minutes < 60:
            return "{} minutes ago".format(int(seconds // 60))
        elif hours < 24:
            return "{} hours ago".format(int(diff.seconds // (60 * 60)))
        elif diff.days == 1:
            return "yesterday"
        elif diff.days < 7:
            return "{} days ago".format(int(seconds // (60 * 60 * 24)))
        elif diff.days < 14:
            return date.strftime("last %A")
        else:
            return date.strftime("%A, %B %d, %Y")
    else:
        diff = date - datetime.now()

        seconds = diff.total_seconds()
        minutes = seconds // 60
        hours = minutes // 60

        if minutes <= 1:
            return "moments ago"
        elif minutes < 60:
            return "in {} minutes".format(int(seconds // 60))
        elif hours < 24:
            return "in {} hours".format(int(diff.seconds // (60 * 60)))
        elif diff.days == 1:
            return "tomorrow"
        elif diff.days < 7:
            return "in {} days".format(int(seconds // (60 * 60 * 24)))
        elif diff.days < 14:
            return date.strftime("next %A")
        else:
            return date.strftime("%A, %B %d, %Y")