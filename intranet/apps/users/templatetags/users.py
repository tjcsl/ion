# -*- coding: utf-8 -*-

import logging

from django import template

from intranet.middleware import threadlocals
from ..models import User

register = template.Library()
logger = logging.getLogger(__name__)


@register.filter
def user_attr(username, attribute):
    """Gets an attribute of the user with the given username."""
    return getattr(User.get_user(username=username), attribute)


@register.filter
def argument_request_user(obj, funcName):
    """Pass request.user as an argument to the given function call."""
    func = getattr(obj, funcName)
    request = threadlocals.request()
    if request:
        return func(request.user)
