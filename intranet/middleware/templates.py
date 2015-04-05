# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import re
from django.conf import settings

logger = logging.getLogger(__name__)


class StripNewlinesMiddleware(object):

    """Strip extra newlines from rendered templates to
    enhance readability.
    """

    def process_response(self, request, response):
        """Process the response and strip extra newlines from HTML."""
        is_html = (response["Content-Type"] == "text/html" or
                   response["Content-Type"].startswith("text/html;"))
        if is_html and settings.DEBUG:
            response.content = re.sub(r'\n(\s*)\n', '\n', response.content.decode("utf-8"))
            response.content = re.sub(r'^(\s*)\n', '', response.content.decode("utf-8"))
        return response


class AdminSelectizeLoadingIndicatorMiddleware(object):

    """Automatically add a loading placeholder for Selectize inputs
    in admin templates.

    This is probably not a good practice, but it really needs to be done
    server-side for the loading indicators to show up instantly.

    """

    def process_response(self, request, response):
        is_html = (response["Content-Type"] == "text/html" or
                   response["Content-Type"].startswith("text/html;"))
        if is_html and request.path.startswith("/eighth/admin"):
            replacement = """</select>
                <div class="selectize-control selectize-loading">
                    <div class="selectize-input disabled">
                        <input type="text" value="Loading..." disabled>
                    </div>
                </div>
                """
            response.content = re.sub(r'</select>', replacement, response.content.decode("utf-8"))
        return response
