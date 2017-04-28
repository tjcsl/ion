# -*- coding: utf-8 -*-

import bleach

ALLOWED_TAGS = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'strong', 'ul', 'iframe', 'div', 'p']
ALLOWED_ATTRIBUTES = {
    'acronym': ['title'],
    'a': ['href', 'title'],
    'abbr': ['title'],
    'iframe': ['src', 'height', 'width', 'allowfullscreen', 'frameborder']
}


def safe_html(txt):
    return bleach.linkify(bleach.clean(txt, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES), skip_tags=['iframe'])
