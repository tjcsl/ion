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
        if response["Content-Type"] == "text/html" and settings.DEBUG:
            response.content = re.sub(r'\n(\s*)\n', '\n', response.content)
            response.content = re.sub(r'^(\s*)\n', '', response.content)
        return response
