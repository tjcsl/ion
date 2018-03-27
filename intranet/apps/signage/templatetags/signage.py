from django import template
from django.template.loader import render_to_string

from .. import pages

register = template.Library()


@register.filter(name="render_page")
def render_page(page):
    """ Renders the template at page.template
    """
    template_name = page.template if page.template else page.name
    template = "signage/pages/{}.html".format(template_name)
    if page.function:
        context_method = getattr(pages, page.function)
    else:
        context_method = getattr(pages, page.name)
    context = context_method()
    return render_to_string(template, context)
