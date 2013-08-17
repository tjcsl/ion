import logging
import re

logger = logging.getLogger(__name__)


class StripNewlinesMiddleware(object):

    """Strip extra newlines from rendered templates to
    enhance readability.
    """

    def process_response(self, request, response):
    	"""
    		Process the response and check if the Content-Type
    		is text/html (a HTML page) and if so strip extra newlines.
    	"""
        if response["Content-Type"] == "text/html":
            response.content = re.sub(r'\n(\s*)\n', '\n', response.content)
            response.content = re.sub(r'^(\s*)\n', '', response.content)
        return response
