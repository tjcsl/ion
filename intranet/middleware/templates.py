import logging
import re

from django.conf import settings

logger = logging.getLogger(__name__)


class StripNewlinesMiddleware:
    """Strip extra newlines from rendered templates to enhance readability."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """Process the response and strip extra newlines from HTML."""
        response = self.get_response(request)
        is_html = response["Content-Type"] == "text/html" or response["Content-Type"].startswith("text/html;")
        if is_html and settings.DEBUG:
            response.content = re.sub(r"\n(\s*)\n", "\n", response.content.decode())
            response.content = re.sub(r"^(\s*)\n", "", response.content.decode())
        return response


class AdminSelectizeLoadingIndicatorMiddleware:
    """Automatically add a loading placeholder for Selectize inputs in admin templates.

    This is probably not a good practice, but it really needs to be done
    server-side for the loading indicators to show up instantly.

    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        is_html = response["Content-Type"] == "text/html" or response["Content-Type"].startswith("text/html;")
        if is_html and request.path.startswith("/eighth/admin"):
            replacement = """</select>
                <div class="selectize-control selectize-loading">
                    <div class="selectize-input disabled">
                        <input type="text" value="Loading..." disabled>
                    </div>
                </div>
                """

            response.content = re.sub(r"</select>", replacement, response.content.decode())
        return response


class NoReferrerMiddleware:
    """Set all links to have rel='noreferrer noopener' to prevent malicious JS from editing what the user sees"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        is_html = response["Content-Type"] == "text/html" or response["Content-Type"].startswith("text/html;")
        if is_html:
            response.content = re.sub(r'<a(.*href ?= ?[\'"]http.*)>', r'<a rel="noopener noreferrer"\1>', response.content.decode())
        return response
