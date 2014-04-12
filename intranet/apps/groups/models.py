from django.db import models

class Group(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=1000, blank=True)
    users = models.ManyToManyField('users.User', null=True)

    def __unicode__(self):
        return "{} ({} users)".format(self.name, len(self.users.all()))
