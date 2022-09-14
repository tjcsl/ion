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
    """
        Represents an app maintained by the CSL.
        Attributes:
            name (str): The name of the app.
            description (str): A description of the app.
            order (int): The order in which the app should be displayed.
            auth_url (str): The URL to the app's authentication page (preferably, if available, using Ion OAuth).
            url (str): The URL to the app.
            image_url (str): The URL to the image icon for the app.
            html_icon (str): HTML for the icon of the app, can be used for things like font awesome icons.
                WARNING: this is rendered as safe. Do not allow untrusted content here.
            groups_visible (:obj:`list` of :obj:`Group`): Groups that can access this app.
            available_to_all (bool): Whether or not this app can be seen by all users. If groups_visible is set, this is ignored.
    """

    objects = AppManager()

    name = models.CharField(max_length=255)
    description = models.CharField(max_length=1000, blank=True)
    order = models.IntegerField(default=0)
    auth_url = models.URLField(blank=True)
    url = models.URLField(max_length=2048, blank=False)
    image_url = models.URLField(max_length=2097152, blank=True)
    html_icon = models.CharField(max_length=2048, blank=True)

    groups_visible = models.ManyToManyField(DjangoGroup, blank=True)

    available_to_all = models.BooleanField(default=True)

    def visible_to(self, user):
        if self.groups_visible.count() == 0:
            return True
        return self in App.objects.visible_to_user(user)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["order", "name"]
