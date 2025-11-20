import json
import logging

from django.conf import settings
from django.utils import timezone

from ..apps.logs.models import Request

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

        if "x-real-ip" in request.headers:
            ip = request.headers["x-real-ip"]
        else:
            ip = (request.META.get("REMOTE_ADDR", ""),)

        if isinstance(ip, set):
            ip = ip[0]

        user_agent = request.headers.get("user-agent", "")
        path = request.get_full_path()

        if user_agent and not (
                any(path.startswith(path_beginning) for path_beginning in settings.NONLOGGABLE_PATH_BEGINNINGS)
                or any(path.endswith(path_ending) for path_ending in settings.NONLOGGABLE_PATH_ENDINGS)
        ):
            log_line = f'{ip} - {username} - [{timezone.localtime()}] "{path}" "{user_agent}"'
            logger.info(log_line)

            request._read_started = False
            request_body = request.body.decode("utf-8") if request.body else ""
            r = Request.objects.create(
                ip=ip,
                path=path,
                user_agent=user_agent,
                method=request.method,
                request=json.dumps(
                    {
                        "GET": dict(request.GET),
                        "POST": dict(request.POST),
                        "META": {k: v for k, v in request.META.items() if not k.startswith("HTTP")},  # HTTP headers are already logged
                        # "FILES": dict(request.FILES),  # TODO: add support for logging files
                        # 'COOKIES': dict(request.COOKIES),  # already logged in headers
                        "headers": dict(request.headers),
                        "method": request.method,
                        "body": request_body,
                        "content_type": request.content_type,
                        "content_params": request.content_params,
                    }, default=str
                ),
            )

            # Redact passwords
            r_request = json.loads(r.request)
            if "password" in r_request["POST"]:
                r_request["POST"]["password"] = "***REDACTED***"
                r.request = json.dumps(r_request)
                r.save()
            if "password" in r_request["body"]:
                idx = r_request["body"].index("password=")
                length = r_request["body"][idx:].index("&") if "&" in r_request["body"][idx:] else len(r_request["body"][idx:])
                r_request["body"] = r_request["body"][:idx] + "password=***REDACTED***" + r_request["body"][idx + length:]
                r.request = json.dumps(r_request)
                r.save()

            if request.user and not request.user.is_anonymous:
                r.user = request.user
                r.save()

        return response
