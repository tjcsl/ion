# -*- coding: utf-8 -*-

import logging

from django import template

from ..users.models import User

register = template.Library()
logger = logging.getLogger(__name__)


@register.filter
def from_cache(value, attribute):
    """ Gets the related attribute from the user object's cache"""
    if not isinstance(value, User):
        raise TypeError("Value must be a User object.")
    if not isinstance(attribute, str):
        raise TypeError("Attribute must be a string.")
    logger.debug("Retrieved attribute `{}` from cache for User `{}`".format(attribute, value))
    return value.get_from_cache(attribute)
