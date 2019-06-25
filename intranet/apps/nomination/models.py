
from django.db import models
from ..users.models import User


class NominationPosition(models.Model):
    """Represents a position that people will be nominated for"""
    position_name = models.CharField(max_length=100)


class Nomination(models.Model):
    """Represents a user nominating another user for a position"""
    nominator = models.ForeignKey(User, related_name="nomination_votes", on_delete=models.CASCADE)
    nominee = models.ForeignKey(User, related_name="nomination_votes_received", on_delete=models.CASCADE)
    position = models.ForeignKey(NominationPosition, related_name="nominations", on_delete=models.CASCADE)
