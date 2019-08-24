from django.conf import settings
from django.db import models


class NominationPosition(models.Model):
    """Represents a position that people will be nominated for"""

    position_name = models.CharField(max_length=100)


class Nomination(models.Model):
    """Represents a user nominating another user for a position"""

    nominator = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="nomination_votes", on_delete=models.CASCADE)
    nominee = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="nomination_votes_received", on_delete=models.CASCADE)
    position = models.ForeignKey(NominationPosition, related_name="nominations", on_delete=models.CASCADE)
