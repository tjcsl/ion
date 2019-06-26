from django.conf import settings
from django.db import models


class SeniorEmailForward(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    email = models.EmailField()

    def __str__(self):
        return "{}".format(self.user)
