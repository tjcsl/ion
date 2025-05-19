from django.contrib.auth.models import Group as DjangoGroup
from django.db import models
from django.db.models import Manager, Q


class AppManager(Manager):
    def visible_to_user(self, user):
        """Get a list of apps available to a given user.

        Same logic as Announcements and Events.

        """
        return App.objects.filter(Q(groups_visible__in=user.groups.all()) | Q(groups_visible__isnull=True)).distinct()


class App(models.Model):
    """Represents an app maintained by TJ CSL."""

    objects = AppManager()

    name = models.CharField(max_length=255)
    description = models.CharField(max_length=1000, blank=True)
    order = models.IntegerField(default=0)
    oauth_application = models.ForeignKey("oauth.CSLApplication", on_delete=models.CASCADE, null=True, blank=True)
    auth_url = models.URLField(blank=True)
    url = models.URLField(max_length=2048, blank=False)
    image_url = models.CharField(max_length=2048, blank=True)
    html_icon = models.CharField(max_length=2048, blank=True)
    invert_image_color_for_dark_mode = models.BooleanField(default=False)

    groups_visible = models.ManyToManyField(DjangoGroup, blank=True)

    def visible_to(self, user):
        if self.groups_visible.count() == 0:
            return True
        return self in App.objects.visible_to_user(user)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["order", "name"]
