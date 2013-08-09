from django.db import models
from intranet.apps.users.models import User


class EighthBlock(models.Model):
    date = models.DateField(null=False)
    block = models.CharField(null=False, max_length=1)
    locked = models.BooleanField(null=False)

    def __str__(self):
        return "{}: {}".format(str(self.date), self.block)


class EighthActivity(models.Model):
    name = models.CharField(null=False, max_length=63)
    # sponsors = models.ManyToManyField(User)
    members = models.ManyToManyField(User, through="EighthSignup")

    # Groups allowed
    # Single students allowed

    def __str__(self):
        return self.name



class EighthScheduledActivity(models.Model):
    pass


class EighthSignup(models.Model):
    user = models.ForeignKey(User, null=False)
    block = models.ForeignKey(EighthBlock, null=False)
    activity = models.ForeignKey(EighthActivity, null=False)

    class Meta:
        unique_together = (("user", "block"),)
        index_together = [
            ["user", "block"],
        ]


class SignupAlert(models.Model):
    user = models.ForeignKey(User, null=False)
    night_before = models.BooleanField(null=False)
    day_of = models.BooleanField(null=False)


class EighthAbsence(models.Model):
    block = models.ForeignKey(EighthBlock)
    user = models.ForeignKey(User)

    class Meta:
        unique_together = (("block", "user"),)