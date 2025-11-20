from django import template

register = template.Library()


@register.filter
def highlight(str1, str2):
    """Highlight str1 with the contents of str2."""
    if isinstance(str2, list):
        str2 = str2[0]

    if str1 and str2 and isinstance(str2, str):
        return str1.replace(str2, f"<b>{str2}</b>")
    else:
        return str1
