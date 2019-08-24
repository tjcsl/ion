from django.contrib.auth.models import Group as DjangoGroup
from django.db import models
from django.db.models import Manager, Q


"""
    Sample TJ configuration:

        Host.objects.create(name="Computer Systems Lab",
                            code="csl",
                            address="remote.tjhsst.edu",
                            linux=True)

        afs = Host.objects.create(name="CSL AFS Root",
                                  code="afs",
                                  address="remote.tjhsst.edu",
                                  directory="/afs/csl/",
                                  linux=True,
                                  available_to_all=True)

        afs.groups_visible.add(Group.objects.get(name="admin_all"))

"""


class HostManager(Manager):
    def visible_to_user(self, user):
        """Get a list of hosts available to a given user.

        Same logic as Announcements and Events.

        """

        return Host.objects.filter(Q(groups_visible__in=user.groups.all()) | Q(groups_visible__isnull=True)).distinct()


class Host(models.Model):
    objects = HostManager()

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=32)
    address = models.CharField(max_length=255)
    directory = models.CharField(max_length=255, blank=True)

    windows = models.BooleanField(default=False)
    linux = models.BooleanField(default=False)

    groups_visible = models.ManyToManyField(DjangoGroup, blank=True)

    available_to_all = models.BooleanField(default=False)

    def visible_to(self, user):
        if self.groups_visible.count() == 0:
            return True
        return self in Host.objects.visible_to_user(user)

    def __str__(self):
        return "{} ({})".format(self.name, self.code)

    class Meta:
        ordering = ["-linux", "name"]
