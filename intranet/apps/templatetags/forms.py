import logging
import re

from django import template

register = template.Library()
logger = logging.getLogger(__name__)


@register.filter
def is_array_field(field):
    return re.match(r"^.*_(\d+)$", field.name)


@register.filter
def field_array_index(field):
    m = re.match(r"^.*_(\d+)$", field.name)
    if m is not None:
        return int(m.groups()[0])
    return None


@register.filter
def field_array_size(field):
    m = re.match(r"^(.*)_\d+$", field.name)
    if m is None:
        return None

    prefix = m.groups()[0]
    count = 0
    for field_name in field.form.fields.keys():
        if re.match(r"^{}_(\d+)$".format(prefix), field_name):
            count += 1
    return count
