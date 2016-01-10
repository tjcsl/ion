# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from rest_framework import renderers


class JPEGRenderer(renderers.BaseRenderer):
    """Renders binary JPEG data.
    """
    media_type = 'image/jpg'
    format = 'jpg'
    charset = None
    render_style = 'binary'

    def render(self, data, media_type=None, renderer_context=None):
        return data
