import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils.timezone import now

from ..users.models import Email


class UnverifiedEmail(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    email = models.ForeignKey(Email, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    verification_token = models.UUIDField(default=uuid.uuid4, editable=False)

    # Email link is expired if it's older than specified expire time and should be deleted.
    def is_expired(self):
        return now() - self.date_created >= timedelta(hours=settings.UNVERIFIED_EMAIL_EXPIRE_HOURS)
