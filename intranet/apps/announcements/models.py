# -*- coding: utf-8 -*-

from datetime import datetime

from django.contrib.auth.models import Group as DjangoGroup
from django.db import models
from django.db.models import Manager, Q

from ..users.models import User


class AnnouncementManager(Manager):

    def visible_to_user(self, user):
        """Get a list of visible announcements for a given user (usually request.user).

        These visible announcements will be those that either have no
        groups assigned to them (and are therefore public) or those in
        which the user is a member.

        """

        return Announcement.objects.filter(Q(groups__in=user.groups.all()) | Q(groups__isnull=True))

    def hidden_announcements(self, user):
        """Get a list of announcements marked as hidden for a given user (usually request.user).

        These are all announcements visible to the user -- they have just decided to
        hide them.

        """
        ids = user.announcements_hidden.all().values_list("announcement__id")
        return Announcement.objects.filter(id__in=ids)


class AnnouncementUserMap(models.Model):
    """Represents mapping fields between announcements and users.

    These attributes would be a part of the Announcement model, but if they are,
    the last updated date is changed whenever a student sees or hides an announcement.

    Access these through announcement.user_map

    If you are checking to see whether a user has hidden an announcement, use:
        Announcement.objects.hidden_announcements(user)

    Attributes:
        announcement
            The one-to-one mapping between this object and the Announcement it is for
        users_hidden
            A many-to-many field of Users who have hidden this announcement
        users_seen
            A many-to-many field of Users who have seen this announcement

    """
    announcement = models.OneToOneField("Announcement", related_name="_user_map")
    users_hidden = models.ManyToManyField(User, blank=True, related_name="announcements_hidden")
    users_seen = models.ManyToManyField(User, blank=True, related_name="announcements_seen")

    def __str__(self):
        return "UserMap: {}".format(self.announcement.title)


class Announcement(models.Model):
    """Represents an announcement.

    Attributes:
        title
            The title of the announcement
        content
            The HTML content of the news post
        authors
            The name of the author
        added
            The date the announcement was added
        updated
            The most recent date the announcement was updated
        user_map
            An attribute corresponding with an AnnouncementUserMap object.
            A new object is automatically created if it does not exist.

    """

    objects = AnnouncementManager()

    title = models.CharField(max_length=127)
    content = models.TextField()
    author = models.CharField(max_length=63, blank=True)
    user = models.ForeignKey(User, null=True, blank=True)
    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    groups = models.ManyToManyField(DjangoGroup, blank=True)

    expiration_date = models.DateTimeField(auto_now=False, default=datetime(3000, 1, 1))

    notify_post = models.BooleanField(default=True)
    notify_email_all = models.BooleanField(default=False)

    pinned = models.BooleanField(default=False)

    def get_author(self):
        return self.author if self.author else self.user.full_name

    def __str__(self):
        return self.title

    @property
    def user_map(self):
        try:
            return self._user_map
        except AnnouncementUserMap.DoesNotExist:
            return AnnouncementUserMap.objects.create(announcement=self)

    @property
    def is_this_year(self):
        """Return whether the announcement was created after September 1st of this school year."""
        now = datetime.now().date()
        ann = self.added.date()
        if now.month < 9:
            return ((ann.year == now.year and ann.month < 9) or (ann.year == now.year - 1 and ann.month >= 9))
        else:
            return ann.year == now.year and ann.month >= 9

    @property
    def dashboard_type(self):
        return "announcement"
    

    class Meta:
        ordering = ["-pinned", "-added"]


class AnnouncementRequest(models.Model):
    """Represents a request for an announcement.

    Attributes:
        title
            The title of the announcement
        content
            The HTML content of the news post
        notes
            Notes for the person who approves the announcement
        added
            The date the request was added
        updated
            The most recent date the request was updated
        user
            The user who submitted the request
        teachers_requested
            The teachers requested to approve the request
        teachers_approved
            The teachers who have approved the request
        posted
            ForeignKey to Announcement if posted
        posted_by
            The user (administrator) that approved the request
        rejected
            Boolean describing whether the post was rejected by
            an administrator. This will hide it.
        admin_email_sent
            Boolean describing whether an email was sent to an
            Intranet administrator to post the announcement.

    """

    title = models.CharField(max_length=127)
    content = models.TextField()
    author = models.CharField(max_length=63, blank=True)

    expiration_date = models.DateTimeField(auto_now=False, default=datetime(3000, 1, 1))
    notes = models.TextField(blank=True)

    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(User, null=True, blank=True, related_name="user")

    teachers_requested = models.ManyToManyField(User, blank=False, related_name="teachers_requested")
    teachers_approved = models.ManyToManyField(User, blank=True, related_name="teachers_approved")

    posted = models.ForeignKey(Announcement, null=True, blank=True)
    posted_by = models.ForeignKey(User, null=True, blank=True, related_name="posted_by")

    rejected = models.BooleanField(default=False)
    rejected_by = models.ForeignKey(User, null=True, blank=True, related_name="rejected_by")

    admin_email_sent = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["-added"]
