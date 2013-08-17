from datetime import datetime
from django import template

register = template.Library()


@register.filter
def fuzzy_date(date):
    """Formats a :class:`datetime.datetime` object relative to the current time"""
    date = date.replace(tzinfo=None)
    diff = datetime.now() - date
    if diff.seconds <= 60:
        return "Moments ago"
    elif diff.seconds <= 60 * 60:
        return "{} minutes ago".format(diff.minutes)
    elif diff.seconds <= 60 * 60 * 23:
        return "{} hours ago".format(diff.seconds // (60 * 60))
    elif diff.days == 1:
        return "Yesterday"
    elif diff.days < 7:
        return "{} days ago".format(diff.days)
    elif diff.days < 14:
        return date.strftime("Last %A")
    else:
        return date.strftime("%A, %B %d, %Y")