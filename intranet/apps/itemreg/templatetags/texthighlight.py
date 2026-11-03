from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def highlight(str1, str2):
    """Highlight occurrences of str2 within str1, escaping all values."""
    if isinstance(str2, list):
        str2 = str2[0]

    if str1 and str2 and isinstance(str2, str):
        # Coerce to str so non-string values (e.g. screen_size) can be split.
        parts = str(str1).split(str2)
        if len(parts) > 1:
            return mark_safe(f"<b>{escape(str2)}</b>".join(escape(part) for part in parts))

    return str1
