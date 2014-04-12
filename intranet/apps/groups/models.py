from django.db import models

class Group(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=1000, blank=True)
    users = models.ManyToManyField('users.User', null=True)
