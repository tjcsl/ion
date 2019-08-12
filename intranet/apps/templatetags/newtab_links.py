import re

from django import template

register = template.Library()


@register.filter(is_safe=True)
def replace_newtab_links(value):
    return re.sub(r'<a(.*?href ?= ?[\'"]http.*?)>', r'<a target="_blank"\1>', value)
