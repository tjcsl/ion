import logging
import string

from django import template

register = template.Library()
logger = logging.getLogger(__name__)


@register.filter
def contains_digit(s):
    return any(c in string.digits for c in s)


@register.filter
def endswith(val, arg):
    return val.endswith(arg)
