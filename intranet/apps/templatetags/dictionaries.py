import logging

from django import template

register = template.Library()
logger = logging.getLogger(__name__)


@register.filter
def lookup(d, key):
    return d[key]
