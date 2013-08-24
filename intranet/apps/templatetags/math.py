import logging
from django import template

register = template.Library()
logger = logging.getLogger(__name__)


@register.filter
def round_to_places(number, precision=0):
    """Rounds a number to a given precision in decimal digits
    (default 0 digits) and returns the integer value.

    Precision may be negative. A precision of 1 will round to the tenths
    place and a precision of -1 will round to the tens place.

    Returns:
        Float

    """

    return round(number, precision)


@register.filter
def to_int(num):
    """Converts a number to an integer."""

    return int(num)


@register.filter
def percent(dividend, divisor):
    """Return the quotient of the arguments as an integer percentage.

    Returns 0 if the divisor is 0.

    """
    try:
        return int(100.0 * dividend / divisor)
    except ZeroDivisionError:
        return 0


@register.filter
def divide(dividend, divisor):
    """Returns the quotient of the arguments as a float."""

    return 1.0 * dividend / divisor