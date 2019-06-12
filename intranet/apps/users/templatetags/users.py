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
    return getattr(User.objects.get(username=username), attribute)


@register.filter
def argument_request_user(obj, func_name):
    """Pass request.user as an argument to the given function call."""
    func = getattr(obj, func_name)
    request = threadlocals.request()
    if request:
        return func(request.user)

    return None
