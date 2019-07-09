from rest_framework import renderers


class JPEGRenderer(renderers.BaseRenderer):
    """Renders binary JPEG data."""

    media_type = "image/jpg"
    format = "jpg"
    charset = None  # type: str
    render_style = "binary"

    def render(self, data, accepted_media_type=None, renderer_context=None):  # pylint: disable=unused-argument
        return data
