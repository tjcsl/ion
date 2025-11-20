from rest_framework.renderers import JSONRenderer

from django.utils.html import escapejs


def safe_json(obj):
    return escapejs(
        JSONRenderer()
        .render(obj)
        .decode("utf-8")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('\\"', "&quot;")
        .replace("'", "&#39;")
    )
