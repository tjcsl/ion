from django.db import models


class Group(models.Model):
    name = models.CharField(null=False, unique=True, max_length=100)
    description = models.CharField(max_length=200)
