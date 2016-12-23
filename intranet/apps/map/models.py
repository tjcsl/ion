from django.db import models


class Room(models.Model):
    svg_id = models.CharField(primary_key=True, unique=True)
    name = models.CharField(max_length=256)
