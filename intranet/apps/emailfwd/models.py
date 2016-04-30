from django.db import models
from ..users.models import User


class SeniorEmailForward(models.Model):
    user = models.ForeignKey(User)
    email = models.EmailField()

    def __str__(self):
        return "{}".format(self.user)

