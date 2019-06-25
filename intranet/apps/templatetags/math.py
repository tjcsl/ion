import logging

from django import template

register = template.Library()
logger = logging.getLogger(__name__)


@register.filter
def round_num(number, precision=0):
    """Rounds a number to a given precision in decimal digits (default 0 digits) and returns the
    integer value.

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
def divide(dividend, divisor):
    """Returns the quotient of the arguments as a float."""

    try:
        return 1.0 * dividend / divisor
    except ZeroDivisionError:
        return 0.0


@register.filter
def multiply(num1, num2):
    """Returns the product of the arguments."""

    return num1 * num2


@register.filter
def minimum(num1, num2):
    """Returns smaller of two numbers."""

    return min(num1, num2)


@register.filter
def maximum(num1, num2):
    """Returns smaller of two numbers."""

    return max(num1, num2)
