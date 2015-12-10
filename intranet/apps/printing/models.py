from django.db import models
from ..users.models import User

class PrintJob(models.Model):
    user = models.ForeignKey(User, null=True, blank=True)
    printer = models.CharField(max_length=100)
    file = models.FileField()
    time = models.DateTimeField(auto_now_add=True)