import logging
from datetime import datetime

logger = logging.getLogger("intranet_access")


class AccessLogMiddleWare(object):

    def process_response(self, request, response):
        if request.user.is_anonymous():
            username = "anonymous_user"
        else:
            username = request.user.username

        log_line = "{} - {} - [{}] \"{}\" \"{}\"".format(
            request.META.get("REMOTE_ADDR", ""),
            username,
            datetime.now(),
            request.path,
            request.META.get("HTTP_USER_AGENT", "")
        )

        logger.info(log_line)

        return response
