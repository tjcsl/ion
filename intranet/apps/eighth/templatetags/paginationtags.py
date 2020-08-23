from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def update_page(context, page_number):
    """Preserve sorting and filtering for pagination"""
    request = context.get("request").GET.copy()
    request["page"] = page_number
    return request.urlencode()
