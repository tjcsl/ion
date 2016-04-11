# -*- coding: utf-8 -*-

from django import template

register = template.Library()


@register.filter
def highlight(str1, str2):
    """Highlight str1 with the contents of str2."""
    if str1 and str2:
        return str1.replace(str2, "<b>{}</b>".format(str2))
    else:
        return str1
