from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def multiline(address):
    result = "{}<br>{}, {} {}".format(address.street, address.city,
                                      address.state, address.postal_code)
    return mark_safe(result)
