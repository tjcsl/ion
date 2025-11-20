from django import template

register = template.Library()


@register.filter
def dashes(phone):
    """Returns the phone number formatted with dashes."""
    if isinstance(phone, str):
        if phone.startswith("+1"):
            return "1-" + "-".join((phone[2:5], phone[5:8], phone[8:]))
        elif len(phone) == 10:
            return "-".join((phone[:3], phone[3:6], phone[6:]))
        else:
            return phone
    else:
        return phone
