import logging

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger("intranet_access")


class AccessLogMiddleWare:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if not request.user:
            username = "unknown_user"
        elif request.user.is_anonymous:
            username = "anonymous_user"
        else:
            username = request.user.username

        if "HTTP_X_REAL_IP" in request.META:
            ip = request.META["HTTP_X_REAL_IP"]
        else:
            ip = (request.META.get("REMOTE_ADDR", ""),)

        if isinstance(ip, set):
            ip = ip[0]

        user_agent = request.META.get("HTTP_USER_AGENT", "")
        log_line = '{} - {} - [{}] "{}" "{}"'.format(ip, username, timezone.localtime(), request.get_full_path(), user_agent)

        if user_agent and not any(user_agent_substring in user_agent for user_agent_substring in settings.NONLOGGABLE_USER_AGENT_SUBSTRINGS):
            logger.info(log_line)

        return response
