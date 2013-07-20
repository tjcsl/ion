from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def multiline(address):
    """Returns the HTML for an address formatted in two lines."""
    result = "{}<br>{}, {} {}".format(address.street, address.city,
                                      address.state, address.postal_code)
    return mark_safe(result)
