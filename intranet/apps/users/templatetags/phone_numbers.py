from django import template

register = template.Library()


@register.filter
def dashes(phone):
    """Returns the phone number formatted with dashes."""
    if isinstance(phone, str):
        if len(phone) == 10:
            return '-'.join((phone[:3], phone[3:6], phone[6:]))
        else:
            return phone
    else:
        return phone
