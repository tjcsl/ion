from django import template
from django.template.loader import render_to_string

from .. import pages

register = template.Library()


@register.filter(name="render_page")
def render_page(page, page_args):
    """ Renders the template at page.template
    """
    print(page_args)
    template_name = page.template if page.template else page.name
    template_fname = "signage/pages/{}.html".format(template_name)
    if page.function:
        context_method = getattr(pages, page.function)
    else:
        context_method = getattr(pages, page.name)
    sign, request = page_args
    context = context_method(page, sign, request)
    return render_to_string(template_fname, context)
