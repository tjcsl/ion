# -*- coding: utf-8 -*-
import logging
from datetime import datetime

logger = logging.getLogger("intranet_access")


class AccessLogMiddleWare(object):

    def process_response(self, request, response):
        if request.user.is_anonymous():
            username = "anonymous_user"
        else:
            username = request.user.username

        if "HTTP_X_FORWARDED_FOR" in request.META:
            ip = request.META["HTTP_X_FORWARDED_FOR"]
        else:
            ip = request.META.get("REMOTE_ADDR", ""),

        if isinstance(ip, set):
            ip = ip[0]

        log_line = "{} - {} - [{}] \"{}\" \"{}\"".format(
            ip,
            username,
            datetime.now(),
            request.get_full_path(),
            request.META.get("HTTP_USER_AGENT", "")
        )

        logger.info(log_line)

        return response
