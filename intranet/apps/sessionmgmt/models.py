from importlib import import_module

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

# Create your models here.

SessionStore = import_module(settings.SESSION_ENGINE).SessionStore


class TrustedSession(models.Model):
    DEVICE_TYPES = (("mobile", "Mobile"), ("tablet", "Tablet"), ("computer", "Computer"), ("unknown", "Unknown type"))

    description = models.CharField(max_length=100)
    device_type = models.CharField(max_length=8, choices=DEVICE_TYPES)

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40)

    first_trusted_date = models.DateTimeField(auto_now_add=True)

    @classmethod
    def delete_expired_sessions(cls, *, user=None) -> None:
        """Deletes all expired trusted sessions for the given user. If ``user`` is ``None`` or not given, deletes all expired trusted sessions.

        Args:
            user: The user to delete all expired trusted sessions for, or ``None`` to delete all expired trusted sessions

        """
        trusted_sessions = cls.objects.all()
        if user is not None:
            trusted_sessions = trusted_sessions.filter(user=user)

        for trusted_session in trusted_sessions:
            if not SessionStore(session_key=trusted_session.session_key).exists(trusted_session.session_key):
                trusted_session.delete()

    class Meta:
        unique_together = (("user", "session_key"),)
