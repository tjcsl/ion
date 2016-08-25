# -*- coding: utf-8 -*-
from django.db import models

from ..users.models import User


class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comments = models.CharField(max_length=50000)
    date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return "{} - {}".format(self.user, self.date)
