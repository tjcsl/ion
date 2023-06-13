from django.conf import settings
from django.db import models


class Request(models.Model):
    """
    This model is used to store access logs.  It is not used by any other
    part of the intranet.
    """

    timestamp = models.DateTimeField(auto_now_add=True)
    ip = models.CharField(max_length=255, verbose_name="IP address")
    path = models.CharField(max_length=255)
    user_agent = models.CharField(max_length=255)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    flag = models.CharField(max_length=255, null=True, blank=True, help_text="Flag this request for review by assigning it a label.")
    request = models.JSONField(null=True, blank=True)  # Serialized HttpRequest object
    method = models.CharField(max_length=255, null=True, blank=True)  # request method

    @property
    def username(self):
        if self.user:
            return self.user.username
        return "unknown_user"

    def __str__(self):
        return f"""{self.ip} - {self.user} - [{self.timestamp}] "{self.path}" "{self.user_agent}" """

    class Meta:
        ordering = ["-timestamp"]
