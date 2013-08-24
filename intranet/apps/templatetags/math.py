import logging
from django import template

register = template.Library()
logger = logging.getLogger(__name__)


@register.filter
def round(number, precision=0):
    """Rounds a number to a given precision in decimal digits
    (default 0 digits) and returns the integer value.

    Precision may be negative. A precision of 1 will round to the tenths
    place and a precision of -1 will round to the tens place.

    Returns:
        Float

    """

    return round(number, precision)


@register.filter
def int(number):
    """Rounds a number to the nearest integer."""

    return int(round(number))


@register.filter
def divide(dividend, divisor):
    """Divide a number by the number passed as an argument.

    Returns 0 if the divisor is 0.

    """
    try:
        return dividend / divisor
    except ZeroDivisionError:
        return 0