# -*- coding: utf-8 -*-

from rest_framework import renderers


class JPEGRenderer(renderers.BaseRenderer):
    """Renders binary JPEG data.
    """
    media_type = 'image/jpg'
    format = 'jpg'
    charset = None  # type: str
    render_style = 'binary'

    def render(self, data, media_type=None, renderer_context=None):
        return data
