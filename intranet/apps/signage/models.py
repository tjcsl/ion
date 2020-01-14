from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class PageQuerySet(models.query.QuerySet):
    def order_properly(self) -> "models.query.QuerySet[Page]":
        """Returns a QuerySet containing all the pages in this QuerySet, but sorted in ascending
        order by their ``order`` field (falling back on ``id`` when the ``order``
        fields for two pages are the same).

        Returns:
            A QuerySet containing all the pages in this QuerySet sorted by their ``order`` and
            ``id`` fields in ascending order.

        """
        return self.order_by("order", "id")


class Page(models.Model):
    """
        iframe: True if page is just an iframe
        url: url for iframe (if iframe is True)
        sandbox: whether the iframe should be sandboxed
                 https://developer.mozilla.org/en-US/docs/Web/HTML/Element/iframe#attr-sandbox

        template: the path to the template (for server side rendering)
        button: the name of the fontawesome icon (ex: "fa-chrome")
        order: index at which button should be placed

        strip_links: whether we strip the links in the iframe (to prevent navigation away)

        signs: set of signs which display this Page
    """

    objects = PageQuerySet.as_manager()

    name = models.CharField(max_length=50)

    iframe = models.BooleanField(default=False)
    url = models.URLField(null=True, blank=True)
    sandbox = models.BooleanField(default=True)

    template = models.CharField(max_length=50, null=True, blank=True)
    function = models.CharField(max_length=50, null=True, blank=True)
    button = models.CharField(max_length=140, null=True, blank=True)
    order = models.IntegerField(default=0)

    strip_links = models.BooleanField(default=True)

    def deploy_to(self, displays=None, exclude=None):
        """
        Deploys page to listed display (specify with display). If display is None,
        deploy to all display. Can specify exclude for which display to exclude.
        This overwrites the first argument.
        """
        if exclude is None:
            exclude = []

        if displays is None:
            signs = Sign.objects.all()
        else:
            signs = Sign.objects.filter(display__in=displays)
        for sign in signs.exclude(display__in=exclude):
            sign.pages.add(self)
            sign.save()

    def __str__(self):
        if self.iframe:
            url = self.url[:10]
            url = url + "..." if len(self.url) > 10 else url
            return "{} ({})".format(self.name, url)
        else:
            return "{}".format(self.name)


class SignQuerySet(models.query.QuerySet):
    def filter_offline(self) -> "models.query.QuerySet[Sign]":
        return self.filter(
            models.Q(latest_heartbeat_time__isnull=True)
            | models.Q(latest_heartbeat_time__lte=timezone.localtime() - timedelta(seconds=settings.SIGNAGE_HEARTBEAT_OFFLINE_TIMEOUT_SECS))
        )

    def filter_online(self) -> "models.query.QuerySet[Sign]":
        return self.filter(
            latest_heartbeat_time__isnull=False,
            latest_heartbeat_time__gt=timezone.localtime() - timedelta(seconds=settings.SIGNAGE_HEARTBEAT_OFFLINE_TIMEOUT_SECS),
        )


class Sign(models.Model):
    """
        name: friendly display name [required]
        display: unique name (should match hostname of pi/compute stick) [required]

        eighth_block_increment: ...
        landscape: if display is in landscape orientation
        map_location: location of display on map

        lock_page: if set, the signage will only display this page
        default_page: if set, the signage will revert to this page after a set
                      amount of time
        day_end_switch_page: A page to switch to near the end of the day
        day_end_switch_minutes: The number of minutes before the end of the day to switch
            to day_end_switch_page. Can be negative to switch after the end of the day.
        latest_heartbeat_time: If the sign has an open websocket connection to a
            SignageConsumer, this is the time at which the last message was received from
            it. If the sign does not have such a connection open, this is None (even if
            the sign previously had an open connection).
        pages: a list of pages
    """

    objects = SignQuerySet.as_manager()

    name = models.CharField(max_length=1000)
    display = models.CharField(max_length=100, unique=True)
    eighth_block_increment = models.IntegerField(default=0, null=True, blank=True)
    landscape = models.BooleanField(default=False)
    map_location = models.CharField(max_length=20, null=True, blank=True)
    img_path = models.CharField(max_length=250, default="https://c1.staticflickr.com/5/4331/36927945575_c2c09e44db_k.jpg")

    lock_page = models.ForeignKey(Page, on_delete=models.SET_NULL, null=True, blank=True, related_name="_unused_1")
    default_page = models.ForeignKey(Page, on_delete=models.SET_NULL, null=True, blank=True, related_name="_unused_2")
    pages = models.ManyToManyField(Page, related_name="signs")

    day_end_switch_page = models.ForeignKey(
        Page, on_delete=models.SET_NULL, null=True, blank=True, related_name="+", help_text="Switch to this page near the end of the day"
    )
    day_end_switch_minutes = models.IntegerField(
        default=5, null=False, blank=False, help_text="Switch pages this many minutes before the end of the day"
    )

    # This can be set to None at any time if the
    latest_heartbeat_time = models.DateTimeField(null=True, default=None)

    @property
    def is_offline(self) -> bool:
        return self.latest_heartbeat_time is None or timezone.localtime() - self.latest_heartbeat_time >= timedelta(
            seconds=settings.SIGNAGE_HEARTBEAT_OFFLINE_TIMEOUT_SECS
        )

    def __str__(self):
        return "{} ({})".format(self.name, self.display)
