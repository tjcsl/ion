# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from ..users.models import User


class PrintJob(models.Model):
    user = models.ForeignKey(User, null=True, blank=True)
    printer = models.CharField(max_length=100)
    file = models.FileField(upload_to="uploads/")
    time = models.DateTimeField(auto_now_add=True)
    printed = models.BooleanField(default=False)
    num_pages = models.IntegerField(default=0)

    def __str__(self):
        return "{} by {} to {}".format(self.file, self.user, self.printer)
