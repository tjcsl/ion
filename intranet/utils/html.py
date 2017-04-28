# -*- coding: utf-8 -*-

import bleach

ALLOWED_TAGS = bleach.sanitizer.ALLOWED_TAGS + ['iframe', 'div', 'p']
ALLOWED_ATTRIBUTES = bleach.sanitizer.ALLOWED_ATTRIBUTES
ALLOWED_ATTRIBUTES['iframe'] = ['src', 'height', 'width', 'allowfullscreen', 'frameborder']


def safe_html(txt):
    return bleach.linkify(bleach.clean(txt, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES), skip_tags=['iframe'])
