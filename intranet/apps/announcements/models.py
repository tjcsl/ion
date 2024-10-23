from datetime import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group as DjangoGroup
from django.db import models
from django.db.models import Manager, Q
from django.utils import timezone
from simple_history.models import HistoricalRecords

from ...utils.date import get_date_range_this_year, is_current_year
from ...utils.deletion import set_historical_user
from ...utils.html import nullify_links
from ..eighth.models import EighthActivity, EighthSponsor


class AnnouncementManager(Manager):
    def visible_to_user(self, user):
        """Get a list of visible announcements for a given user (usually request.user).

        These visible announcements will be those that either have no
        groups assigned to them (and are therefore public) or those in
        which the user is a member.

        Apparently this .filter() call occasionally returns duplicates, hence the .distinct()...

        """

        if user.is_restricted:  # Restricted users are not authorized to view announcements
            return Announcement.objects.none()

        return (
            Announcement.objects.filter(
                Q(user=user)
                # even if there are no groups to restrict to, there might still be restrictions on the activity
                | Q(groups__isnull=True) & Q(activity__isnull=True)
                | Q(groups__user=user)
                | Q(announcementrequest__teachers_requested=user)
                | Q(announcementrequest__user=user)
                | Q(activity__restricted=False)
                | Q(activity__isnull=False)
                & (
                    Q(public=True)
                    | Q(activity__users_allowed=user)
                    | Q(activity__groups_allowed__user=user)
                    | (Q(**{f"activity__{user.grade.name_plural}_allowed": True}) if 9 <= int(user.grade) <= 12 else Q(pk__in=[]))
                )
            )
            .distinct()
            .prefetch_related("activity")
        )

    def hidden_announcements(self, user):
        """Get a list of announcements marked as hidden for a given user (usually request.user).

        These are all announcements visible to the user -- they have just decided to
        hide them.

        """
        ids = user.announcements_hidden.all().values_list("announcement__id")
        return Announcement.objects.filter(id__in=ids)

    def this_year(self):
        """Get AnnouncementRequests from this school year only."""
        start_date, end_date = get_date_range_this_year()
        return Announcement.objects.filter(added__gte=start_date, added__lte=end_date)


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

    announcement = models.OneToOneField("Announcement", related_name="_user_map", on_delete=models.CASCADE)
    users_hidden = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="announcements_hidden")
    users_seen = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="announcements_seen")

    def __str__(self):
        return f"UserMap: {self.announcement.title}"


class Announcement(models.Model):
    """Represents an announcement.

    Attributes:
        title
            The title of the announcement
        content
            The HTML content of the news post
        author
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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=set_historical_user)
    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    groups = models.ManyToManyField(DjangoGroup, blank=True)
    public = models.BooleanField(
        default=False,
        help_text=(
            "Restricted activities have announcements that are only visible to members of the activity. "
            "Enabling this will make the announcement visible to all users."
        ),
    )

    activity = models.ForeignKey(EighthActivity, null=True, blank=True, on_delete=models.CASCADE)

    expiration_date = models.DateTimeField(auto_now=False, default=timezone.make_aware(datetime(3000, 1, 1)))

    notify_post = models.BooleanField(default=True)
    notify_email_all = models.BooleanField(default=False)

    pinned = models.BooleanField(default=False)

    history = HistoricalRecords()

    def get_author(self) -> str:
        """Returns 'author' if it is set. Otherwise, returns the name of the user who created the announcement.

        Returns:
            The name of the author as it should be displayed with the announcement.

        """
        return self.author if self.author else self.user.full_name_nick if self.user else None

    def __str__(self):
        return self.title

    @property
    def user_map(self):
        try:
            return self._user_map  # pylint: disable=no-member; Defined via a related_name in AnnouncementUserMap
        except AnnouncementUserMap.DoesNotExist:
            return AnnouncementUserMap.objects.create(announcement=self)

    @property
    def is_this_year(self):
        """Return whether the announcement was created after July 1st of this school year."""
        return is_current_year(self.added)

    @property
    def is_club_announcement(self):
        return self.activity is not None

    def is_visible(self, user):
        return self in Announcement.objects.visible_to_user(user)

    def can_modify(self, user):
        return (
            user.is_announcements_admin
            or self.is_club_announcement
            and (
                user in self.activity.officers.all()
                or user in self.activity.club_sponsors.all()
                or EighthSponsor.objects.filter(user=user).exists()
                and user.sponsor_obj in self.activity.sponsors.all()
            )
        )

    # False, not None. This can be None if no AnnouncementRequest exists for this Announcement,
    # and we should not reevaluate in that case.
    _announcementrequest = False  # type: AnnouncementRequest

    @property
    def announcementrequest(self):
        if self._announcementrequest is False:
            self._announcementrequest = self.announcementrequest_set.first()

        return self._announcementrequest

    def is_visible_requester(self, user):
        try:
            return self.announcementrequest_set.filter(teachers_requested=user).exists()
        except get_user_model().DoesNotExist:
            return False

    def is_visible_submitter(self, user):
        try:
            return self.user == user or self.announcementrequest and user == self.announcementrequest.user
        except get_user_model().DoesNotExist:
            return False

    @property
    def dashboard_type(self):
        return "announcement"

    @property
    def content_no_links(self) -> str:
        """Returns the content of this announcement with all links nullified.

        Returns:
            The content of this announcement with all links nullified.

        """
        return nullify_links(self.content)

    class Meta:
        ordering = ["-pinned", "-added"]


class AnnouncementRequestQuerySet(models.query.QuerySet):
    def this_year(self):
        """Get AnnouncementRequests from this school year only."""
        start_date, end_date = get_date_range_this_year()
        return self.filter(added__gte=start_date, added__lte=end_date)


class AnnouncementRequestManager(Manager):
    def get_queryset(self):
        return AnnouncementRequestQuerySet(self.model, using=self._db)


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

    objects = AnnouncementRequestManager()

    title = models.CharField(max_length=127)
    content = models.TextField()
    author = models.CharField(max_length=63, blank=True)

    expiration_date = models.DateTimeField(auto_now=False, default=timezone.make_aware(datetime(3000, 1, 1)))
    notes = models.TextField(blank=True)

    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="user", on_delete=set_historical_user)

    teachers_requested = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=False, related_name="teachers_requested")
    teachers_approved = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="teachers_approved")

    posted = models.ForeignKey(Announcement, null=True, blank=True, on_delete=models.CASCADE)
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="posted_by", on_delete=set_historical_user)

    rejected = models.BooleanField(default=False)
    rejected_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="rejected_by", on_delete=set_historical_user)

    admin_email_sent = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["-added"]


class WarningAnnouncement(models.Model):
    """Warning in yellow to show on Ion"""

    title = models.CharField(max_length=127)
    content = models.TextField(help_text="Content of the warning. You can use HTML here.")
    type = models.CharField(
        max_length=127,
        choices=[
            ("dashboard", "Dashboard Warning (displays on dashboard)"),
            ("login", "Login Warning (displays on login page)"),
            ("dashboard_login", "Dashboard and Login Warning (displays on dashboard and login pages)"),
            ("global", "Global Warning (displays on all pages)"),
        ],
        default="dashboard",
    )
    active = models.BooleanField(default=True, help_text="Whether or not to show the warning.")
    added = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    @property
    def show_on_dashboard(self):
        return self.type in ("dashboard", "dashboard_login")  # global is not included. It will show on all pages and this logic isn't needed.

    @property
    def show_on_login(self):
        return self.type in ("login", "dashboard_login")

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["-added"]
