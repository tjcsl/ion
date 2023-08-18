import pytz

from django.conf import settings
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

    @property
    def is_this_year(self):
        """Return whether the enrichment activity was created after the start of the school year."""
        return is_current_year(self.added)

    @property
    def happened(self):
        """Return whether an enrichment activity has happened."""
        return self.time < timezone.now()

    @property
    def is_today(self):
        """Return whether the enrichment activity is happening today."""
        return self.time.date().astimezone(pytz.timezone("US/Eastern")) == timezone.now().date().astimezone(pytz.timezone("US/Eastern"))

    def __str__(self):
        return "{} - {}".format(self.title, self.time)

    class Meta:
        ordering = ["time"]
        verbose_name_plural = "enrichment activities"
