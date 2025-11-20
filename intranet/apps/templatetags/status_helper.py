from urllib.parse import urlparse, urlunparse

from django import template
from django.core.cache import cache

from intranet import settings
from intranet.apps.emerg.views import get_csl_status

register = template.Library()


@register.simple_tag
def get_cache(key):
    return cache.get(key)


class GetCSLStatusNode(template.Node):
    def render(self, context):
        context["csl_status"] = get_csl_status()
        return ""


@register.tag
def get_csl_status_from_cache(parser, token):
    tokens = token.contents.split()
    if len(tokens) == 1:
        return GetCSLStatusNode()
    else:
        raise template.TemplateSyntaxError("Usage: {% get_csl_status_from_cache %} {{ csl_status }}")


@register.simple_tag
def get_csl_status_page_url():
    parsed_url = urlparse(settings.CSL_STATUS_PAGE)

    return urlunparse((parsed_url.scheme, parsed_url.netloc, "", "", "", ""))
