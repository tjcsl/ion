from django.db import models
from intranet.apps.users.models import User


class EighthBlock(models.Model):
    date = models.DateField(null=False)
    block = models.CharField(null=False, max_length=1)
    locked = models.BooleanField(null=False)


class EighthActivity(models.Model):
    name = models.CharField(null=False, max_length=63)
    # sponsors = models.ManyToManyField(User)
    members = models.ManyToManyField(User, through="EighthSignup")


class EighthScheduledActivity(models.Model):
    pass


class EighthSignup(models.Model):
    user = models.ForeignKey(User)
    block = models.ForeignKey(EighthBlock)
    activity = models.ForeignKey(EighthActivity)

    class Meta:
        unique_together = (("user", "block"),)
        index_together = [
            ["user", "block"],
        ]
