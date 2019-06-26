from django.conf import settings
from django.db import models


class LostItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=100)
    description = models.TextField(max_length=1000)
    last_seen = models.DateField()
    added = models.DateTimeField(auto_now_add=True)
    found = models.BooleanField(default=False)

    def __str__(self):
        return "{}".format(self.title)

    class Meta:
        ordering = ["-added"]


class FoundItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=100)
    description = models.TextField(max_length=1000)
    found = models.DateField()
    added = models.DateTimeField(auto_now_add=True)
    retrieved = models.BooleanField(default=False)

    def __str__(self):
        return "{}".format(self.title)

    class Meta:
        ordering = ["-added"]
