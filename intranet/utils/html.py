import urllib.parse
from typing import Mapping, Optional, Tuple, Union

import bleach
from bleach.css_sanitizer import CSSSanitizer

tags = ["a", "abbr", "acronym", "b", "br", "blockquote", "code", "em", "hr", "i", "li", "ol", "strong", "ul", "iframe", "img", "div", "p"]

att = {
    "acronym": ["title"],
    "a": ["href", "title"],
    "abbr": ["title"],
    "iframe": ["src", "height", "width", "allowfullscreen", "frameborder"],
    "img": ["src", "alt", "title", "style"],
}

css_sanitizer = CSSSanitizer(allowed_css_properties=["width", "height", "float",
                                                     "margin-left", "margin-right", "margin-top",
                                                     "margin-bottom", "margin", "border",
                                                     "border-style", "border-width"])


def safe_html(txt):
    return bleach.linkify(bleach.clean(txt, tags=tags, attributes=att, css_sanitizer=css_sanitizer))


def link_removal_callback(  # pylint: disable=unused-argument
    attrs: Mapping[Union[str, Tuple[Optional[str]]], str], new: bool = False
) -> Optional[Mapping[Union[str, Tuple[Optional[str]]], str]]:
    """Internal callback for ``nullify_links()``."""
    for key in tuple(attrs.keys()):
        if isinstance(key, tuple) and "href" in key:
            attrs[key] = "javascript:void(0)"

    return attrs


def nullify_links(text: str) -> str:
    """Given a string containing HTML, changes the ``href`` attribute of any links to "javascript:void(0)" to render
    the link useless.

    Args:
        text: The HTML string in which links should be nullified.

    Returns:
        The HTML string with all links nullified.

    """
    return bleach.linkify(text, [link_removal_callback])


def safe_fcps_emerg_html(text: str, base_url: str) -> str:
    def translate_link_attr(  # pylint: disable=unused-argument
        attrs: Mapping[Union[str, Tuple[Optional[str]]], str], new: bool = False
    ) -> Optional[Mapping[Union[str, Tuple[Optional[str]]], str]]:
        for key in tuple(attrs.keys()):
            if isinstance(key, tuple) and "href" in key:
                # Translate links that don't specify a protocol/host
                # For example, /a/b will be translated to (something like) https://fcps.edu/a/b
                attrs[key] = urllib.parse.urljoin(base_url, attrs[key])

        return attrs

    return bleach.linkify(
        bleach.clean(text, strip=True, tags=tags, attributes=att, css_sanitizer=css_sanitizer), [translate_link_attr]
    )
