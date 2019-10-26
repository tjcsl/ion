from django.conf import settings
from django.db import models
from django.utils import timezone

from .helpers import get_feature_context

# Create your models here.


class FeatureAnnouncementQuerySet(models.QuerySet):
    def filter_active(self):
        """Filter to just the feature announcements that are currently 'active'.

        Returns:
            The ``QuerySet`` of just ``FeatureAnnouncement``s that are currently 'active' (past their
            activation date, but not their expiration date).

        """
        today = timezone.localdate()
        return self.filter(activation_date__lte=today, expiration_date__gte=today)

    def filter_show_for_user(self, user):
        """Filter to just the feature announcements that should be shown for the given user.

        For example, this excludes users who have "dismissed" the feature announcement.

        Args:
            user: The user to filter the feature announcements to show for.

        Returns:
            The ``QuerySet`` of just ``FeatureAnnouncement``s that should be shown for the given user

        """
        return self.exclude(users_dismissed=user)

    def filter_for_context(self, context: str):
        """Filter to just the feature announcements that should be shown for the given 'context'.

        Args:
            context: The name of the 'context' to filter feature announcements for, as returned
               by ``helpers.get_feature_context()``.

        Returns:
            The ``QuerySet`` of ``FeatureAnnouncement``s filtered for the given 'context'.

        """
        return self.filter(context=context)

    def filter_for_request(self, request):
        """Filter to just the feature announcements that should be shown for the given request.

        This calls ``filter_active()``, ``filter_show_for_user()``, and ``filter_for_context()``.

        Args:
            request: The request object to filter the feature announcements to show for.

        Returns:
            The ``QuerySet`` of ``FeatureAnnouncement``s filtered for the given request.

        """
        query = self.filter_active().filter_for_context(get_feature_context(request))
        if request.user.is_authenticated:
            query = query.filter_show_for_user(request.user)

        return query


class FeatureAnnouncement(models.Model):
    objects = FeatureAnnouncementQuerySet.as_manager()

    # Both INCLUSIVE
    activation_date = models.DateField(null=False, blank=False)
    expiration_date = models.DateField(null=False, blank=False)

    CONTEXTS = (("dashboard", "dashboard"), ("login", "login"), ("eighth_signup", "eighth_signup"))

    context = models.CharField(max_length=20, choices=CONTEXTS)

    # WARNING: This is rendered as 'safe' to allow things like links. Do NOT allow untrusted content here.
    announcement_html = models.CharField(
        max_length=1024, null=False, blank=False, help_text="The HTML for the feature announcement (do NOT allow untrusted content)"
    )

    # Users who have seen the announcement
    users_seen = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="feature_announcements_seen")
    # Users who have clicked the "close" button to dismiss the announcement
    users_dismissed = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="feature_announcements_dismissed")

    def __repr__(self):
        return "<FeatureAnnouncement {} with context {} from {} to {}>".format(
            self.id, self.context, self.activation_date.strftime("%Y-%m-%d"), self.expiration_date.strftime("%Y-%m-%d")
        )

    def __str__(self):
        return repr(self)
