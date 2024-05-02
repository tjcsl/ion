import json

from django.conf import settings
from django.db import models


class Request(models.Model):
    """
    This model is used to store access logs.  It is not used by any other
    part of the intranet.
    """

    timestamp = models.DateTimeField(auto_now_add=True)
    ip = models.TextField(verbose_name="IP address")
    path = models.TextField()
    user_agent = models.TextField()

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    flag = models.CharField(max_length=255, null=True, blank=True, help_text="Flag this request for review by assigning it a label.")
    request = models.JSONField(null=True, blank=True)  # Serialized HttpRequest object
    method = models.TextField(null=True, blank=True)  # request method

    @property
    def username(self):
        return self.user.username if self.user else "anonymous"

    @property
    def request_json(self):
        return json.dumps(json.loads(self.request), indent=4, sort_keys=True).replace('\\"', "'")

    @property
    def request_json_obj(self):
        return json.loads(self.request)

    def __str__(self):
        return f'{self.timestamp.astimezone(settings.PYTZ_TIME_ZONE).strftime("%b %d %Y %H:%M:%S")} - {self.username} - {self.ip} - {self.method} "{self.path}"'  # pylint: disable=line-too-long # noqa: E501

    class Meta:
        ordering = ["-timestamp"]
