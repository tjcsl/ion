import datetime

from django.conf import settings
from django.contrib.auth.models import Group as DjangoGroup
from django.db import models
from django.db.models import Manager
from django.utils import timezone

from ...utils.date import get_date_range_this_year, is_current_year
from ...utils.deletion import set_historical_user


class EnrichmentActivityQuerySet(models.query.QuerySet):
    def this_year(self):
        """Get enrichment activities created during this school year.

        Returns:
            Enrichment activities created during this school year.
        """
        start_date, end_date = get_date_range_this_year()
        return self.filter(added__gte=start_date, added__lte=end_date)


class EnrichmentActivityManager(Manager):
    def get_queryset(self):
        return EnrichmentActivityQuerySet(self.model, using=self._db)

    def visible_to_user(self, *args):  # , user):
        """Get a list of visible enrichment activities for a given user (usually request.user).

        TODO: implement this method. Add group restrictions.
        """

        return EnrichmentActivity.objects.all().this_year()


class EnrichmentActivity(models.Model):
    """An enrichment activity available to the TJ community."""

    objects = EnrichmentActivityManager()

    title = models.CharField(max_length=100)
    description = models.TextField(max_length=10000)
    added = models.DateTimeField(auto_now=True)

    time = models.DateTimeField(blank=True, null=True)
    location = models.CharField(max_length=300)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=set_historical_user)

    capacity = models.SmallIntegerField(default=28)
    attending = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="enrichments_attending")

    presign = models.BooleanField(default=False)

    groups_allowed = models.ManyToManyField(DjangoGroup, related_name="allowed_enrichments_set", blank=True)
    groups_blacklisted = models.ManyToManyField(DjangoGroup, related_name="blacklisted_enrichments_set", blank=True)

    def user_can_signup(self, user):
        """Return whether a user can sign up for an enrichment activity.

        Args:
            user: The user to check.

        Returns:
            Whether the user can sign up for the enrichment activity.
        """
        return (not self.groups_allowed.exists() or any(group in user.groups.all() for group in self.groups_allowed.all())) and not any(
            group in user.groups.all() for group in self.groups_blacklisted.all()
        )

    def user_is_blacklisted(self, user):
        return any(group in user.groups.all() for group in self.groups_blacklisted.all())

    @property
    def is_this_year(self):
        """Return whether the enrichment activity was created after the start of the school year."""
        return is_current_year(self.added)

    @property
    def happened(self):
        """Return whether an enrichment activity has happened."""
        return self.time < timezone.now()

    @property
    def restricted(self):
        return self.groups_allowed.exists()

    @property
    def is_too_early_to_signup(self):
        """Returns whether it is too early to sign up for the activity
        if it is a presign.
        This contains the 2 day presign logic.

        Returns:
            Whether it is too early to sign up for this scheduled activity
            and when the activity opens for signups.
        """
        now = timezone.localtime()

        # Midnight of the day of the activity
        activity_date = self.time.astimezone(timezone.get_default_timezone())
        activity_date = datetime.datetime.combine(activity_date.date(), datetime.time(0, 0, 0), tzinfo=activity_date.tzinfo)

        presign_period = datetime.timedelta(minutes=settings.EIGHTH_PRESIGNUP_HOURS * 60 + settings.EIGHTH_PRESIGNUP_MINUTES)

        return (now < (activity_date - presign_period), activity_date - presign_period)

    def __str__(self):
        return "{} - {}".format(self.title, self.time)

    class Meta:
        ordering = ["time"]
        verbose_name_plural = "enrichment activities"
