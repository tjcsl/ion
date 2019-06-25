import bleach

ALLOWED_TAGS = ['a', 'abbr', 'acronym', 'b', 'br', 'blockquote', 'code', 'em', 'hr', 'i', 'li', 'ol', 'strong', 'ul', 'iframe', 'img', 'div', 'p']

ALLOWED_ATTRIBUTES = {
    'acronym': ['title'],
    'a': ['href', 'title'],
    'abbr': ['title'],
    'iframe': ['src', 'height', 'width', 'allowfullscreen', 'frameborder'],
    'img': ['src', 'alt', 'title', 'style']
}

ALLOWED_STYLES = [
    'width', 'height', 'float', 'margin-left', 'margin-right', 'margin-top', 'margin-bottom', 'margin', 'border', 'border-style', 'border-width'
]


def safe_html(txt):
    return bleach.linkify(bleach.clean(txt, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, styles=ALLOWED_STYLES))
