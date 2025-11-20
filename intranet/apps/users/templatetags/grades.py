from django import template

from ..models import Grade

register = template.Library()


@register.filter
def to_grade_number(year):
    """Returns a `Grade` object for a year."""
    return Grade(year).number


@register.filter
def to_grade_name(year):
    """Returns a `Grade` object for a year."""
    return Grade(year).name
