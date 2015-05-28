# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import template
from ..models import User

register = template.Library()


@register.filter
def user_attr(username, attribute):
    """Gets an attribute of the user with the given username."""
    return getattr(User.get_user(username=username), attribute)
