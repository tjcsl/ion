# -*- coding: utf-8 -*-

from django.db import models

from ..users.models import User


class PrintJob(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    printer = models.CharField(max_length=100)
    file = models.FileField(upload_to="printing/")
    page_range = models.CharField(blank=True, max_length=100)
    time = models.DateTimeField(auto_now_add=True)
    printed = models.BooleanField(default=False)
    num_pages = models.IntegerField(default=0)
    duplex = models.BooleanField(default=True)

    def __str__(self):
        return "{} by {} to {}".format(self.file, self.user, self.printer)
