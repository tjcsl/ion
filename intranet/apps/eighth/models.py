# pylint: disable=C0302; Allow more than 1000 lines
# pylint: enable=pointless-string-statement
import datetime
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group as DjangoGroup
from django.core.cache import cache
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.db import models, transaction
from django.db.models import Manager, Q, Count
from django.utils import formats
from simple_history.models import HistoricalRecords

from . import exceptions as eighth_exceptions
from ..notifications.emails import email_send
from ...utils.date import is_current_year, get_date_range_this_year
from ...utils.deletion import set_historical_user

logger = logging.getLogger(__name__)


class AbstractBaseEighthModel(models.Model):
    """Abstract base model that includes created and last modified times."""

    created_time = models.DateTimeField(auto_now_add=True, null=True)
    last_modified_time = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        abstract = True


class EighthSponsor(AbstractBaseEighthModel):
    """Represents a sponsor for an eighth period activity.

    A sponsor could be linked to an actual user or just a name.

    Attributes:
        first_name
            The first name of the sponsor
        last_name
            The last name of the sponsor
        user
            A :class:`users.User` object
            linked to the sponsor.
        online_attendance
            Whether the sponsor takes attendance online.
        contracted_eighth
            Whether the sponsor is contracted to supervise 8th periods.
        show_full_name
            Whether to always show the sponsor's full name
            (e.x. because there are two teachers named Lewis)

    """
    DEPARTMENTS = (("general", "General"),
                   ("math_cs", "Math/CS"),
                   ("english", "English"),
                   ("social_studies", "Social Studies"),
                   ("fine_arts", "Fine Arts"),
                   ("health_pe", "Health/PE"),
                   ("scitech", "Science/Technology"))

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=set_historical_user)
    department = models.CharField(max_length=20, choices=DEPARTMENTS, default="general")
    full_time = models.BooleanField(default=True)
    online_attendance = models.BooleanField(default=True)
    contracted_eighth = models.BooleanField(default=True)
    show_full_name = models.BooleanField(default=False)

    history = HistoricalRecords()

    class Meta:
        unique_together = (("first_name", "last_name", "user",
                            "online_attendance", "full_time", "department"),)
        ordering = (
            "last_name",
            "first_name",
        )

    @property
    def name(self):
        if self.show_full_name and self.first_name:
            return self.last_name + ", " + self.first_name
        else:
            return self.last_name

    @property
    def to_be_assigned(self):
        return any(x in self.name.lower() for x in ["to be assigned", "to be determined", "to be announced"])

    def __str__(self):
        return self.name


class EighthRoom(AbstractBaseEighthModel):
    """Represents a room in which an eighth period activity can be held.

    Attributes:
        name
            The name of the room.
        capacity
            The maximum capacity of the room (-1 for unlimited, 0 to prevent student signup)

    """
    name = models.CharField(max_length=100)
    capacity = models.SmallIntegerField(default=28)
    available_for_eighth = models.BooleanField(default=True)

    history = HistoricalRecords()

    unique_together = (("name", "capacity"),)

    @staticmethod
    def total_capacity_of_rooms(rooms):
        capacity = 0
        for r in rooms:
            if r.capacity == -1:
                return -1
            capacity += r.capacity
        return capacity

    @property
    def formatted_name(self):
        if self.name[0].isdigit():  # All rooms starting with an integer will be prefixed
            return "Rm. {}".format(self.name)
        if self.name.startswith('Room'):  # Some room names are prefixed with 'Room'; for consistency
            return "Rm. {}".format(self.name[5:])
        return self.name

    @property
    def to_be_determined(self):
        return any(x in self.name.lower() for x in ["to be assigned", "to be determined", "to be announced"])

    def __str__(self):
        return "{} ({})".format(self.name, self.capacity)

    class Meta:
        ordering = ("name",)


class EighthActivityExcludeDeletedManager(models.Manager):
    def get_queryset(self):
        return super(EighthActivityExcludeDeletedManager, self).get_queryset().exclude(deleted=True)


class EighthActivity(AbstractBaseEighthModel):
    """Represents an eighth period activity.

    Attributes:
        name
            The name of the activity, max length 100 characters.
        description
            The description of the activity, shown on the signup page below the other information.
            Information on an EighthScheduledActivity basis can be found in the "comments" field
            of that model. Max length 2000 characters.
        sponsors
            The default activity-level sponsors for the activity. On an EighthScheduledActivity basis,
            you should NOT query this field. Use scheduled_activity.get_true_sponsors()
        rooms
            The default activity-level rooms for the activity. On an EighthScheduledActivity basis,
            you should NOT query this field. Use scheduled_activity.get_true_rooms()
        default_capacity
            The default capacity, which overrides the sum of the default rooms when scheduling the
            activity. By default, this has a null value and is ignored.
        presign
            If True, the activity can only be signed up for within 48 hours of the day that the activity
            is scheduled.
        one_a_day
            If True, a student can only sign up for one instance of this activity per day.
        both_blocks
            If True, a signup for an EighthScheduledActivity during an A or B block will enforce and
            automatically trigger a signup on the other block. Does not enforce signups for blocks other
            than A and B.
        sticky
            If True, then students who sign up or are placed in this activity cannot switch out of it.
            A sticky activity should also be restricted, unless you're mean.
        special
            If True, then the activity receives a special designation on the signup list, and is stuck
            to the top of the list.
        administrative
            If True, then students cannot see the activity in their signup list. However, the activity still
            exists in the system and can be seen by administrators. Students can still sign up for the activity
            through the API -- this does not prevent students from signing up for it, and just merely hides it
            from view. An administrative activity should be restricted.
        finance
            If True, then the club has an account with the finance office.
        users_allowed
            Individual users allowed to sign up for this activity. Extensive use of this is discouraged; make
            a group instead through the "Add and Assign Empty Group" button on the Edit Activity page. Only
            takes effect if the activity is restricted.
        groups_allowed
            Individual groups allowed to sign up for this activity. Only takes effect if the activity is
            restricted.
        users_blacklisted
            Individual users who are not allowed to sign up for this activity. Only takes effect if the activity
            is not restricted.
        freshman_allowed, sophomores_allowed, juniors_allowed, seniors_allowed
            Whether Freshman/Sophomores/Juniors/Seniors are allowed to sign up for this activity. Only
            takes effect if the activity is restricted.
        wed_a, wed_b, fri_a, fri_b
            What blocks the activity usually meets. Does not affect schedule, is just information for the Eighth Office.
        admin_comments
            Notes for the Eighth Office
        favorites
            A ManyToManyField of User objects who have favorited the activity.
        deleted
            Whether the activity still technically exists in the system, but was marked to be deleted.

    """
    objects = models.Manager()
    undeleted_objects = EighthActivityExcludeDeletedManager()

    name = models.CharField(max_length=100)  # This should really be unique
    description = models.CharField(max_length=2000, blank=True)
    sponsors = models.ManyToManyField(EighthSponsor, blank=True)
    rooms = models.ManyToManyField(EighthRoom, blank=True)
    default_capacity = models.SmallIntegerField(null=True, blank=True)

    presign = models.BooleanField(default=False)
    one_a_day = models.BooleanField(default=False)
    both_blocks = models.BooleanField(default=False)
    sticky = models.BooleanField(default=False)
    special = models.BooleanField(default=False)
    administrative = models.BooleanField(default=False)
    finance = models.CharField(max_length=100, blank=True, null=True)

    restricted = models.BooleanField(default=False)

    users_allowed = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="restricted_activity_set", blank=True)
    groups_allowed = models.ManyToManyField(DjangoGroup, related_name="restricted_activity_set", blank=True)

    users_blacklisted = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)

    freshmen_allowed = models.BooleanField(default=False)
    sophomores_allowed = models.BooleanField(default=False)
    juniors_allowed = models.BooleanField(default=False)
    seniors_allowed = models.BooleanField(default=False)

    wed_a = models.BooleanField("Meets Wednesday A", default=False)
    wed_b = models.BooleanField("Meets Wednesday B", default=False)
    fri_a = models.BooleanField("Meets Friday A", default=False)
    fri_b = models.BooleanField("Meets Friday B", default=False)

    admin_comments = models.CharField(max_length=1000, blank=True)

    favorites = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="favorited_activity_set", blank=True)

    similarities = models.ManyToManyField('EighthActivitySimilarity', related_name='activity_set', blank=True)

    deleted = models.BooleanField(blank=True, default=False)

    history = HistoricalRecords()

    def capacity(self):
        # Note that this is the default capacity if the
        # rooms/capacity are not overridden for a particular block.
        if self.default_capacity:
            return self.default_capacity
        else:
            return EighthRoom.total_capacity_of_rooms(self.rooms.all())

    @property
    def aid(self):
        """The publicly visible activity ID."""
        return self.id

    @property
    def name_with_flags(self):
        """Return the activity name with special, both blocks, restricted, administrative, sticky,
        and deleted flags."""
        return self._name_with_flags(True)

    @property
    def name_with_flags_no_restricted(self):
        """Return the activity name with special, both blocks, administrative, sticky, and deleted
        flags."""
        return self._name_with_flags(False)

    def _name_with_flags(self, include_restricted, title=None):
        """Generate the name with flags."""
        name = "Special: " if self.special else ""
        name += self.name
        if title:
            name += " - {}".format(title)

        name += " (R)" if include_restricted and self.restricted else ""
        name += " (BB)" if self.both_blocks else ""
        name += " (A)" if self.administrative else ""
        name += " (S)" if self.sticky else ""
        name += " (Deleted)" if self.deleted else ""
        return name

    @classmethod
    def restricted_activities_available_to_user(cls, user):
        """Find the restricted activities available to the given user."""
        if not user:
            return []

        activities = set(user.restricted_activity_set.values_list("id", flat=True))

        if user and user.grade and user.grade.number and user.grade.name:
            grade = user.grade
        else:
            grade = None

        if grade is not None and 9 <= grade.number <= 12:
            activities |= set(EighthActivity.objects.filter(**{'{}_allowed'.format(grade.name_plural): True}).values_list("id", flat=True))

        for group in user.groups.all():
            activities |= set(group.restricted_activity_set.values_list("id", flat=True))

        return list(activities)

    @classmethod
    def available_ids(cls):
        id_min = 1
        id_max = 3200
        nums = set(range(id_min, id_max))
        used = {row[0] for row in EighthActivity.objects.values_list("id")}
        avail = nums - used
        return list(avail)

    def change_id_to(self, new_id):
        """Changes the internal ID field.

        Possible solution: https://djangosnippets.org/snippets/2691/

        """
        # EighthActivity.objects.filter(pk=self.pk).update(id=new_id)

    def get_active_schedulings(self):
        """Return EighthScheduledActivity's of this activity since the beginning of the year."""
        date_start, date_end = get_date_range_this_year()

        return EighthScheduledActivity.objects.filter(activity=self, block__date__gte=date_start, block__date__lte=date_end)

    @property
    def is_active(self):
        """Return whether an activity is "active." An activity is considered to be active if it has
        been scheduled at all this year."""
        return self.get_active_schedulings().exists()

    @property
    def frequent_users(self):
        """Return a QuerySet of user id's and counts that have signed up for this activity more than
        `settings.SIMILAR_THRESHOLD` times. This is be used for suggesting activities to users."""
        key = "eighthactivity_{}:frequent_users".format(self.id)
        cached = cache.get(key)
        if cached:
            return cached
        freq_users = self.eighthscheduledactivity_set.exclude(
            Q(eighthsignup_set__user=None) | Q(administrative=True) | Q(special=True) | Q(restricted=True)).values('eighthsignup_set__user').annotate(
                count=Count('eighthsignup_set__user')).filter(count__gte=settings.SIMILAR_THRESHOLD).order_by('-count')
        cache.set(key, freq_users, timeout=60 * 60 * 24 * 7)
        return freq_users

    @property
    def is_popular(self):
        return self.frequent_users.count() > (settings.SIMILAR_THRESHOLD * 2)

    class Meta:
        verbose_name_plural = "eighth activities"

    def __str__(self):
        return self.name_with_flags


class EighthBlockQuerySet(models.query.QuerySet):
    def this_year(self):
        """ Get EighthBlocks from this school year only. """
        start_date, end_date = get_date_range_this_year()
        return self.filter(date__gte=start_date, date__lte=end_date)


class EighthBlockManager(models.Manager):
    def get_queryset(self):
        return EighthBlockQuerySet(self.model, using=self._db)

    def get_upcoming_blocks(self, max_number=-1):
        """Gets the X number of upcoming blocks (that will take place in the future). If there is no
        block in the future, the most recent block will be returned.

        Returns: A QuerySet of `EighthBlock` objects

        """

        now = datetime.datetime.now()

        # Show same day if it's before 17:00
        if now.hour < 17:
            now = now.replace(hour=0, minute=0, second=0, microsecond=0)

        blocks = self.order_by("date", "block_letter").filter(date__gte=now)

        if max_number == -1:
            return blocks

        return blocks[:max_number]

    def get_first_upcoming_block(self):
        """Gets the first upcoming block (the first block that will take place in the future). If
        there is no block in the future, the most recent block will be returned.

        Returns: the `EighthBlock` object

        """

        return self.get_upcoming_blocks().first()

    def get_next_upcoming_blocks(self):
        """Gets the next upccoming blocks. (Finds the other blocks that are occurring on the day of
        the first upcoming block.)

        Returns: A QuerySet of `EighthBlock` objects.

        """

        next_block = EighthBlock.objects.get_first_upcoming_block()

        if not next_block:
            return EighthBlock.objects.none()

        next_blocks = EighthBlock.objects.filter(date=next_block.date)
        return next_blocks

    def get_blocks_this_year(self):
        """Get a list of blocks that occur this school year."""

        date_start, date_end = get_date_range_this_year()

        return EighthBlock.objects.filter(date__gte=date_start, date__lte=date_end)


class EighthBlock(AbstractBaseEighthModel):
    r"""Represents an eighth period block.

    Attributes:
        date
            The date of the block.
        signup_time
            The recommended time at which all users should sign up.
            This does *not* prevent people from signing up at this
            time, however students will see the amount of time left
            to sign up. Defaults to 12:40.
        block_letter
            The block letter (e.g. A, B, A1, A2, SOL).
            Despite its name, it can now be more than just a letter.
        locked
            Whether signups are closed.
        activities
            List of :class:`EighthScheduledActivity`\s for the block.
        override_blocks
            List of :class:`EighthBlock`\s that the block overrides.

            This allows the half-blocks used during Techlab visits to be
            easily managed. If a student should only be allowed to sign up
            for either only block A or both blocks A1 and A2, then block A
            would override blocks A1 and A2, and blocks A1 and A2 would
            override block A.
        comments
            A short comments field displayed next to the block letter.

    """

    objects = EighthBlockManager()

    date = models.DateField(null=False)
    signup_time = models.TimeField(default=datetime.time(12, 40))
    block_letter = models.CharField(max_length=10)
    locked = models.BooleanField(default=False)
    activities = models.ManyToManyField(EighthActivity, through="EighthScheduledActivity", blank=True)
    comments = models.CharField(max_length=100, blank=True)

    override_blocks = models.ManyToManyField("EighthBlock", blank=True)

    history = HistoricalRecords()

    def save(self, *args, **kwargs):  # pylint: disable=arguments-differ
        """Capitalize the first letter of the block name."""
        letter = getattr(self, "block_letter", None)
        if letter and len(letter) >= 1:
            self.block_letter = letter[:1].upper() + letter[1:]

        super(EighthBlock, self).save(*args, **kwargs)

    def next_blocks(self, quantity=-1):
        """Get the next blocks in order."""
        blocks = (EighthBlock.objects.get_blocks_this_year().order_by(
            "date", "block_letter").filter(Q(date__gt=self.date) | (Q(date=self.date) & Q(block_letter__gt=self.block_letter))))
        if quantity == -1:
            return blocks
        return blocks[:quantity]

    def previous_blocks(self, quantity=-1):
        """Get the previous blocks in order."""
        blocks = (EighthBlock.objects.get_blocks_this_year().order_by(
            "-date", "-block_letter").filter(Q(date__lt=self.date) | (Q(date=self.date) & Q(block_letter__lt=self.block_letter))))
        if quantity == -1:
            return blocks.reverse()
        return blocks[:quantity].reverse()

    def is_today(self):
        """Does the block occur today?"""
        return datetime.date.today() == self.date

    def signup_time_future(self):
        """Is the signup time in the future?"""
        now = datetime.datetime.now()
        return now.date() < self.date or (self.date == now.date() and self.signup_time > now.time())

    def date_in_past(self):
        """Is the block's date in the past?

        (Has it not yet happened?)

        """
        now = datetime.datetime.now()
        return now.date() > self.date

    def in_clear_absence_period(self):
        """Is the current date in the block's clear absence period?

        (Should info on clearing the absence show?)

        """
        now = datetime.datetime.now()
        two_weeks = self.date + datetime.timedelta(days=settings.CLEAR_ABSENCE_DAYS)
        return now.date() <= two_weeks

    def attendance_locked(self):
        """Is it past 10PM on the day of the block?"""
        now = datetime.datetime.now()
        return now.date() > self.date or (now.date() == self.date and now.time() > datetime.time(settings.ATTENDANCE_LOCK_HOUR, 0))

    def num_signups(self):
        """How many people have signed up?"""
        return EighthSignup.objects.filter(scheduled_activity__block=self, user__in=get_user_model().objects.get_students()).count()

    def num_no_signups(self):
        """How many people have not signed up?"""
        signup_users_count = get_user_model().objects.get_students().count()
        return signup_users_count - self.num_signups()

    def get_unsigned_students(self):
        """Return a list of Users who haven't signed up for an activity."""
        return get_user_model().objects.get_students().exclude(eighthsignup__scheduled_activity__block=self)

    def get_hidden_signups(self):
        """ Return a list of Users who are *not* in the All Students list but have signed up for an activity.
            This is usually a list of signups for z-Withdrawn from TJ """
        return EighthSignup.objects.filter(scheduled_activity__block=self).exclude(user__in=get_user_model().objects.get_students())

    @property
    def letter_width(self):
        return (len(self.block_letter) - 1) * 6 + 15

    @property
    def short_text(self):
        """Display the date and block letter (mm/dd B, for example: '9/1 B')

        """
        return "{} {}".format(self.date.strftime("%m/%d"), self.block_letter)

    @property
    def is_this_year(self):
        """Return whether the block occurs after September 1st of this school year."""
        return is_current_year(datetime.datetime.combine(self.date, datetime.time()))

    @property
    def formatted_date(self):
        return formats.date_format(self.date, settings.EIGHTH_BLOCK_DATE_FORMAT)

    def __str__(self):
        return "{} ({})".format(self.formatted_date, self.block_letter)

    class Meta:
        unique_together = (("date", "block_letter"),)
        ordering = ("date", "block_letter")


class EighthScheduledActivityManager(Manager):
    """Model Manager for EighthScheduledActivity."""

    def for_sponsor(self, sponsor, include_cancelled=False):
        """Return a QueryList of EighthScheduledActivities where the given EighthSponsor is
        sponsoring.

        If a sponsorship is defined in an EighthActivity, it may be overridden
        on a block by block basis in an EighthScheduledActivity. Sponsors from
        the EighthActivity do not carry over.

        EighthScheduledActivities that are deleted or cancelled are also not
        counted.

        """
        sponsoring_filter = (Q(sponsors=sponsor) | (Q(sponsors=None) & Q(activity__sponsors=sponsor)))
        sched_acts = (EighthScheduledActivity.objects.exclude(activity__deleted=True).filter(sponsoring_filter).distinct())
        if not include_cancelled:
            sched_acts = sched_acts.exclude(cancelled=True)

        return sched_acts


class EighthScheduledActivity(AbstractBaseEighthModel):
    r"""Represents the relationship between an activity and a block in which it has been scheduled.

    Attributes:
        block : :class:`EighthBlock`
            The :class:`EighthBlock` during which an
            :class:`EighthActivity` has been scheduled
        activity
            The scheduled :class:`EighthActivity`
        members
            The :class:`User<intranet.apps.users.models.User>`\s who have
            signed up for an :class:`EighthBlock`
        both_blocks
            If True, a signup for an EighthScheduledActivity during an A or B block will enforce and
            automatically trigger a signup on the other block. Does not enforce signups for blocks other
            than A and B.
        comments
            Notes for students
        admin_comments
            Notes for the Eighth Office
        sponsors
            :class:`EighthSponsor`\s that will override the
            :class:`EighthActivity`'s default sponsors
        rooms
            :class:`EighthRoom`\s that will override the
            :class:`EighthActivity`'s default rooms
        attendance_taken
            Whether the :class:`EighthSponsor` for the scheduled
            :class:`EighthActivity` has taken attendance yet
        special
            Whether this scheduled instance of the activity is special. If
            not set, falls back on the EighthActivity's special setting.
        cancelled
            whether the :class:`EighthScheduledActivity` has been cancelled

    """

    # Use model manager
    objects = EighthScheduledActivityManager()

    block = models.ForeignKey(EighthBlock, on_delete=models.CASCADE)
    activity = models.ForeignKey(EighthActivity, on_delete=models.CASCADE)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, through="EighthSignup", related_name="eighthscheduledactivity_set")
    waitlist = models.ManyToManyField(settings.AUTH_USER_MODEL, through="EighthWaitlist", related_name="%(class)s_scheduledactivity_set")

    admin_comments = models.CharField(max_length=1000, blank=True)
    title = models.CharField(max_length=1000, blank=True)
    comments = models.CharField(max_length=1000, blank=True)

    # Overridden attributes
    sponsors = models.ManyToManyField(EighthSponsor, blank=True)
    rooms = models.ManyToManyField(EighthRoom, blank=True)
    capacity = models.SmallIntegerField(null=True, blank=True)
    both_blocks = models.BooleanField(default=False)
    special = models.BooleanField(default=False)
    administrative = models.BooleanField(default=False)
    restricted = models.BooleanField(default=False)
    sticky = models.BooleanField(default=False)

    attendance_taken = models.BooleanField(default=False)
    cancelled = models.BooleanField(default=False)

    archived_member_count = models.SmallIntegerField(null=True, blank=True)

    history = HistoricalRecords()

    def get_scheduled_rooms(self):
        return self.rooms.all() or self.activity.rooms.all()

    @property
    def all_associated_rooms(self):
        return list(self.rooms.all()) + list(self.activity.rooms.all())

    @property
    def full_title(self):
        """Gets the full title for the activity, appending the title of the scheduled activity to
        the activity's name."""
        cancelled_str = " (Cancelled)" if self.cancelled else ""
        act_name = self.activity.name + cancelled_str
        if self.special and not self.activity.special:
            act_name = "Special: " + act_name
        return act_name if not self.title else "{} - {}".format(act_name, self.title)

    @property
    def title_with_flags(self):
        """Gets the title for the activity, appending the title of the scheduled activity to the
        activity's name and flags."""
        cancelled_str = " (Cancelled)" if self.cancelled else ""
        name_with_flags = self.activity._name_with_flags(True, self.title) + cancelled_str  # pylint: disable=protected-access
        if self.special and not self.activity.special:
            name_with_flags = "Special: " + name_with_flags
        return name_with_flags

    def get_true_sponsors(self):
        """Get the sponsors for the scheduled activity, taking into account activity defaults and
        overrides."""
        return self.sponsors.all() or self.activity.sponsors.all()

    def user_is_sponsor(self, user):
        """Return whether the given user is a sponsor of the activity.

        Returns:
            Boolean
        """
        return self.get_true_sponsors().filter(user=user).exists()

    def get_true_rooms(self):
        """Get the rooms for the scheduled activity, taking into account activity defaults and
        overrides."""
        return self.rooms.all() or self.activity.rooms.all()

    def get_true_capacity(self):
        """Get the capacity for the scheduled activity, taking into account activity defaults and
        overrides."""
        if self.capacity is not None:
            return self.capacity

        if self.rooms.count() == 0 and self.activity.default_capacity:
            # use activity-level override
            return self.activity.default_capacity

        return EighthRoom.total_capacity_of_rooms(self.get_true_rooms())

    def is_both_blocks(self):
        return self.both_blocks or self.activity.both_blocks

    def get_restricted(self):
        """Get whether this scheduled activity is restricted."""
        return self.restricted or self.activity.restricted

    def get_sticky(self):
        """Get whether this scheduled activity is sticky."""
        return self.sticky or self.activity.sticky

    def get_finance(self):
        """Get whether this activity has an account with the finance office."""
        return self.activity.finance

    def get_administrative(self):
        """Get whether this scheduled activity is administrative."""
        return self.administrative or self.activity.administrative

    def get_special(self):
        """Get whether this scheduled activity is special, checking the
           activity-level special settings.
        """
        return self.special or self.activity.special

    def is_full(self):
        """Return whether the activity is full."""
        capacity = self.get_true_capacity()
        return capacity != -1 and self.eighthsignup_set.count() >= capacity

    def is_almost_full(self):
        """Return whether the activity is almost full (>90%)."""
        capacity = self.get_true_capacity()
        return capacity != -1 and self.eighthsignup_set.count() >= (0.9 * capacity)

    def is_overbooked(self):
        """Return whether the activity is overbooked."""
        capacity = self.get_true_capacity()
        return capacity != -1 and self.eighthsignup_set.count() > capacity

    def is_too_early_to_signup(self, now=None):
        """Return whether it is too early to sign up for the activity if it is a presign (48 hour
        logic is here)."""
        if now is None:
            now = datetime.datetime.now()

        activity_date = (datetime.datetime.combine(self.block.date, datetime.time(0, 0, 0)))
        # Presign activities can only be signed up for 2 days in advance.
        presign_period = datetime.timedelta(days=2)

        return now < (activity_date - presign_period)

    def has_open_passes(self):
        """Return whether there are passes that have not been acknowledged."""
        return self.eighthsignup_set.filter(after_deadline=True, pass_accepted=False).exists()

    def get_viewable_members(self, user=None):
        """Get the list of members that you have permissions to view.

        Returns: List of members

        """
        members = []
        for member in self.members.all():
            show = member.can_view_eighth or (user and (user.is_eighth_admin or user.is_teacher or member == user))

            if show:
                members.append(member)

        return sorted(members, key=lambda u: (u.last_name, u.first_name))

    def get_viewable_members_serializer(self, request):
        """Get a QuerySet of User objects of students in the activity. Needed for the
        EighthScheduledActivitySerializer.

        Returns: QuerySet

        """
        ids = []
        user = request.user
        for member in self.members.all():
            show = member.can_view_eighth or (user and (user.is_eighth_admin or user.is_teacher or member == user))

            if show:
                ids.append(member.id)

        return get_user_model().objects.filter(id__in=ids)

    def get_hidden_members(self, user=None):
        """Get the members that you do not have permission to view.

        Returns: List of members hidden based on their permission preferences

        """
        hidden_members = []
        for member in self.members.all():
            show = member.can_view_eighth or (user and (user.is_eighth_admin or user.is_teacher or member == user))

            if not show:
                hidden_members.append(member)

        return hidden_members

    def get_both_blocks_sibling(self):
        """If this is a both-blocks activity, get the other EighthScheduledActivity
           object that occurs on the other block.

           both_blocks means A and B block, NOT all of the blocks on that day.

           Returns:
                EighthScheduledActivity object if found
                None if the activity cannot have a sibling
                False if not found
        """
        if not self.is_both_blocks():
            return None

        if self.block.block_letter not in ["A", "B"]:
            # both_blocks is not currently implemented for blocks other than A and B
            return None

        other_block_letter = ("A" if self.block.block_letter == "B" else "B")

        try:
            return EighthScheduledActivity.objects.exclude(pk=self.pk).get(activity=self.activity, block__date=self.block.date,
                                                                           block__block_letter=other_block_letter)
        except EighthScheduledActivity.DoesNotExist:
            return None

    def notify_waitlist(self, waitlists, activity):
        data = {"activity": activity}
        for waitlist in waitlists:
            email_send("eighth/emails/waitlist.txt", "eighth/emails/waitlist.html", data, "Open Spot Notification", [waitlist.user.primary_email])

    @transaction.atomic
    def add_user(self, user, request=None, force=False, no_after_deadline=False, add_to_waitlist=False):
        """Sign up a user to this scheduled activity if possible. This is where the magic happens.

        Raises an exception if there's a problem signing the user up
        unless the signup is forced.

        """
        if request is not None:
            force = (force or ("force" in request.GET)) and request.user.is_eighth_admin
            add_to_waitlist = (add_to_waitlist or ("add_to_waitlist" in request.GET)) and request.user.is_eighth_admin

        exception = eighth_exceptions.SignupException()

        if user.grade and user.grade.number > 12:
            exception.SignupForbidden = True

        all_sched_act = [self]
        all_blocks = [self.block]

        if self.is_both_blocks():
            # Finds the other scheduling of the same activity on the same day
            # See note above in get_both_blocks_sibling()
            sibling = self.get_both_blocks_sibling()

            if sibling:
                all_sched_act.append(sibling)
                all_blocks.append(sibling.block)

        waitlist = None
        if force:
            EighthWaitlist.objects.filter(scheduled_activity_id=self.id, user_id=user.id, block_id=self.block.id).delete()
        else:
            # Check if the user who sent the request has the permissions
            # to change the target user's signups
            if request is not None:
                if user != request.user and not request.user.is_eighth_admin:
                    exception.SignupForbidden = True

            # Check if the activity has been deleted
            if self.activity.deleted:
                exception.ActivityDeleted = True

            # Check if the user is already stickied into an activity
            if EighthSignup.objects.filter(user=user, scheduled_activity__block__in=all_blocks).filter(
                    Q(scheduled_activity__activity__sticky=True) | Q(scheduled_activity__sticky=True)).exists():
                exception.Sticky = True

            for sched_act in all_sched_act:
                # Check if the block has been locked
                if sched_act.block.locked:
                    exception.BlockLocked = True

                # Check if the scheduled activity has been cancelled
                if sched_act.cancelled:
                    exception.ScheduledActivityCancelled = True

                # Check if the activity is full
                if settings.ENABLE_WAITLIST and (add_to_waitlist or  # pylint: disable=too-many-boolean-expressions
                                                 (sched_act.is_full() and not self.is_both_blocks() and
                                                  (request is not None and not request.user.is_eighth_admin and request.user.is_student))):
                    if user.primary_email:
                        if EighthWaitlist.objects.filter(user_id=user.id, block_id=self.block.id).exists():
                            EighthWaitlist.objects.filter(user_id=user.id, block_id=self.block.id).delete()
                        waitlist = EighthWaitlist.objects.create(user=user, block=self.block, scheduled_activity=sched_act)
                    else:
                        exception.PrimaryEmailNotSet = True
                elif sched_act.is_full():
                    exception.ActivityFull = True

            # Check if it's too early to sign up for the activity
            if self.activity.presign:
                if self.is_too_early_to_signup():
                    exception.Presign = True

            # Check if signup would violate one-a-day constraint
            if not self.is_both_blocks() and self.activity.one_a_day:
                in_act = (EighthSignup.objects.exclude(scheduled_activity__block=self.block).filter(
                    user=user, scheduled_activity__block__date=self.block.date, scheduled_activity__activity=self.activity).exists())
                if in_act:
                    exception.OneADay = True

            # Check if user is allowed in the activity if it's restricted
            if self.get_restricted():
                acts = EighthActivity.restricted_activities_available_to_user(user)
                if self.activity.id not in acts:
                    exception.Restricted = True

            # Check if user is blacklisted from activity
            if self.activity.users_blacklisted.filter(username=user).exists():
                exception.Blacklisted = True

        if self.get_sticky():
            EighthWaitlist.objects.filter(user_id=user.id, block_id=self.block.id).delete()

        success_message = "Successfully added to waitlist for activity." if waitlist else "Successfully signed up for activity."
        """
        final_remove_signups = []

        # Check if the block overrides signups on other blocks
        if len(self.block.override_blocks.all()) > 0:
            override_blocks = self.block.override_blocks.all()
            can_change_out = True

            for block in override_blocks:
                # If block is locked, can't change out of
                if block.locked and not force:
                    exception.OverrideBlockLocked = [block]
                    can_change_out = False
                    break

                signup_objs = (EighthSignup.objects
                                           .filter(user=user,
                                                   scheduled_activity__activity__sticky=True,
                                                   scheduled_activity__block=block))
                in_stickie = signup_objs.exists()
                if in_stickie and not force:
                    exception.OverrideBlockPermissions = [signup_objs[0].scheduled_activity.activity, block]
                    can_change_out = False
                    break

            # Going to change out of dependent activities at the end
            if can_change_out:
                for block in override_blocks:
                    ovr_signups = EighthSignup.objects.filter(scheduled_activity__block=block, user=user)
                    for signup in ovr_signups:
                        logger.debug("Need to remove signup for {0}".format(signup))
                        final_remove_signups.append(signup)
        """

        # If we've collected any errors, raise the exception and abort
        # the signup attempt
        if exception.errors:
            raise exception

        # Everything's good to go - complete the signup. If we've gotten to
        # this point, the signup is either before deadline or performed by
        # an eighth period admin, so previous absences and passes are cleared.
        after_deadline = self.block.locked

        # If we're doing an eighth admin action (like signing up a group),
        # don't make an after deadline signup, which creates a pass.
        if no_after_deadline:
            after_deadline = False
        if not waitlist:
            if not self.is_both_blocks():
                try:
                    existing_signup = EighthSignup.objects.get(user=user, scheduled_activity__block=self.block)
                except EighthSignup.DoesNotExist:
                    EighthSignup.objects.create_signup(user=user, scheduled_activity=self, after_deadline=after_deadline)
                else:
                    previous_activity_name = existing_signup.scheduled_activity.activity.name_with_flags
                    prev_sponsors = existing_signup.scheduled_activity.get_true_sponsors()
                    previous_activity_sponsors = ", ".join(map(str, prev_sponsors))
                    previous_activity = existing_signup.scheduled_activity

                    if not existing_signup.scheduled_activity.is_both_blocks():
                        existing_signup.scheduled_activity = self
                        existing_signup.after_deadline = after_deadline
                        existing_signup.was_absent = False
                        existing_signup.absence_acknowledged = False
                        existing_signup.pass_accepted = False
                        existing_signup.previous_activity_name = previous_activity_name
                        existing_signup.previous_activity_sponsors = previous_activity_sponsors

                        existing_signup.save()
                    else:
                        # Clear out the other signups for this block if the user is
                        # switching out of a both-blocks activity
                        sibling = existing_signup.scheduled_activity.get_both_blocks_sibling()
                        existing_blocks = [
                            existing_signup.scheduled_activity.block
                        ]
                        if sibling:
                            existing_blocks.append(sibling.block)
                        logger.debug(existing_blocks)
                        EighthSignup.objects.filter(user=user, scheduled_activity__block__in=existing_blocks).delete()
                        EighthWaitlist.objects.filter(user=user, scheduled_activity=self).delete()
                        EighthSignup.objects.create_signup(user=user, scheduled_activity=self, after_deadline=after_deadline,
                                                           previous_activity_name=previous_activity_name,
                                                           previous_activity_sponsors=previous_activity_sponsors, own_signup=(user == request.user))
                    if settings.ENABLE_WAITLIST and (previous_activity.waitlist.all().exists() and not self.block.locked and request is not None and
                                                     not request.session.get("disable_waitlist_transactions", False)):
                        if not previous_activity.is_full():
                            waitlists = EighthWaitlist.objects.get_next_waitlist(previous_activity)
                            self.notify_waitlist(waitlists, previous_activity)
            else:
                existing_signups = EighthSignup.objects.filter(user=user, scheduled_activity__block__in=all_blocks)

                prev_data = {}
                for signup in existing_signups:
                    prev_sponsors = signup.scheduled_activity.get_true_sponsors()
                    prev_data[signup.scheduled_activity.block.block_letter] = {
                        "name": signup.scheduled_activity.activity.name_with_flags,
                        "sponsors": ", ".join(map(str, prev_sponsors))
                    }
                existing_signups.delete()

                for sched_act in all_sched_act:
                    letter = sched_act.block.block_letter
                    if letter in prev_data:
                        previous_activity_name = prev_data[letter]["name"]
                        previous_activity_sponsors = prev_data[letter]["sponsors"]
                    else:
                        previous_activity_name = None
                        previous_activity_sponsors = None

                    EighthSignup.objects.create_signup(user=user, scheduled_activity=sched_act, after_deadline=after_deadline,
                                                       previous_activity_name=previous_activity_name,
                                                       previous_activity_sponsors=previous_activity_sponsors, own_signup=(user == request.user))

                    # signup.previous_activity_name = signup.activity.name_with_flags
                    # signup.previous_activity_sponsors = ", ".join(map(str, signup.get_true_sponsors()))
        """
        # See "If block overrides signup on other blocks" check
        # If there are EighthSignups that need to be removed, do them at the end
        for signup in final_remove_signups:
            success_message += "\nYour signup for {0} on {1} was removed. ".format(
                signup.scheduled_activity.activity, signup.scheduled_activity.block)
            signup.delete()
        """

        return success_message

    def cancel(self):
        """Cancel an EighthScheduledActivity.

        This does nothing besides set the cancelled flag and save the
        object.

        """
        # super(EighthScheduledActivity, self).save(*args, **kwargs)

        logger.debug("Running cancel hooks: %s", self)

        if not self.cancelled:
            logger.debug("Cancelling %s", self)
            self.cancelled = True
            self.save(update_fields=["cancelled"])
        # NOT USED. Was broken anyway.
        """
        cancelled_room = EighthRoom.objects.get_or_create(name="CANCELLED", capacity=0)[0]
        cancelled_sponsor = EighthSponsor.objects.get_or_create(first_name="", last_name="CANCELLED")[0]
        if cancelled_room not in list(self.rooms.all()):
            self.rooms.all().delete()
            self.rooms.add(cancelled_room)

        if cancelled_sponsor not in list(self.sponsors.all()):
            self.sponsors.all().delete()
            self.sponsors.add(cancelled_sponsor)

        self.save()
        """

    def uncancel(self):
        """Uncancel an EighthScheduledActivity.

        This does nothing besides unset the cancelled flag and save the
        object.

        """

        if self.cancelled:
            logger.debug("Uncancelling %s", self)
            self.cancelled = False
            self.save(update_fields=["cancelled"])
        # NOT USED. Was broken anyway.
        """
        cancelled_room = EighthRoom.objects.get_or_create(name="CANCELLED", capacity=0)[0]
        cancelled_sponsor = EighthSponsor.objects.get_or_create(first_name="", last_name="CANCELLED")[0]
        if cancelled_room in list(self.rooms.all()):
            self.rooms.filter(id=cancelled_room.id).delete()

        if cancelled_sponsor in list(self.sponsors.all()):
            self.sponsors.filter(id=cancelled_sponsor.id).delete()

        self.save()
        """

    def save(self, *args, **kwargs):  # pylint: disable=arguments-differ
        super(EighthScheduledActivity, self).save(*args, **kwargs)

    class Meta:
        unique_together = (("block", "activity"),)
        verbose_name_plural = "eighth scheduled activities"

    def __str__(self):
        cancelled_str = " (Cancelled)" if self.cancelled else ""
        suff = " - {}".format(self.title) if self.title else ""
        return "{}{} on {}{}".format(self.activity, suff, self.block, cancelled_str)


class EighthSignupManager(Manager):
    """Model manager for EighthSignup."""

    def create_signup(self, user, scheduled_activity, **kwargs):
        if EighthSignup.objects.filter(user=user, scheduled_activity__block=scheduled_activity.block).exists():
            raise ValidationError("EighthSignup already exists for this user on this block.")
        self.create(user=user, scheduled_activity=scheduled_activity, **kwargs)

    def get_absences(self):
        return EighthSignup.objects.filter(was_absent=True, scheduled_activity__attendance_taken=True)


class EighthSignup(AbstractBaseEighthModel):
    """Represents a signup/membership in an eighth period activity.

    Attributes:
        user
            The :class:`User<intranet.apps.users.models.User>` who has
            signed up.
        scheduled_activity
            The :class:`EighthScheduledActivity` for which the user
            has signed up.
        after_deadline
            Whether the signup was after deadline.
        previous_activity_name
            The name of the activity the student was previously signed
            up for (used for passes)
        previous_activity_sponsors
            The sponsors of the activity the student was previously
            signed up for.
        pass_accepted
            Whether the pass was accepted
        was_absent
            Whether the student was absent.
        absence_acknowledged
            Whether the student has dismissed the absence notification.
        absence_emailed
            Whether the student has been emailed about the absence.

    """
    objects = EighthSignupManager()

    time = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=False, on_delete=set_historical_user)
    scheduled_activity = models.ForeignKey(EighthScheduledActivity, related_name="eighthsignup_set", null=False, db_index=True,
                                           on_delete=models.CASCADE)

    # An after-deadline signup is assumed to be a pass
    after_deadline = models.BooleanField(default=False)
    previous_activity_name = models.CharField(max_length=200, blank=True, null=True, default=None)
    previous_activity_sponsors = models.CharField(max_length=10000, blank=True, null=True, default=None)

    pass_accepted = models.BooleanField(default=False, blank=True)
    was_absent = models.BooleanField(default=False, blank=True)
    absence_acknowledged = models.BooleanField(default=False, blank=True)
    absence_emailed = models.BooleanField(default=False, blank=True)

    archived_was_absent = models.BooleanField(default=False, blank=True)

    def save(self, *args, **kwargs):  # pylint: disable=arguments-differ
        if self.has_conflict():
            raise ValidationError("EighthSignup already exists for this user on this block.")
        super(EighthSignup, self).save(*args, **kwargs)

    own_signup = models.BooleanField(default=False)

    history = HistoricalRecords()

    def validate_unique(self, *args, **kwargs):  # pylint: disable=arguments-differ
        """Checked whether more than one EighthSignup exists for a User on a given EighthBlock."""
        super(EighthSignup, self).validate_unique(*args, **kwargs)

        if self.has_conflict():
            raise ValidationError({NON_FIELD_ERRORS: ("EighthSignup already exists for the User and the EighthScheduledActivity's block",)})

    def has_conflict(self):
        signup_count = EighthSignup.objects.exclude(pk=self.pk).filter(user=self.user,
                                                                       scheduled_activity__block=self.scheduled_activity.block).count()
        return signup_count > 0

    def remove_signup(self, user=None, force=False, dont_run_waitlist=False):
        """Attempt to remove the EighthSignup if the user has permission to do so."""

        exception = eighth_exceptions.SignupException()

        if user is not None:
            if user != self.user and not user.is_eighth_admin:
                exception.SignupForbidden = True

        # Check if the block has been locked
        if self.scheduled_activity.block.locked:
            exception.BlockLocked = True

        # Check if the scheduled activity has been cancelled
        if self.scheduled_activity.cancelled:
            exception.ScheduledActivityCancelled = True

        # Check if the activity has been deleted
        if self.scheduled_activity.activity.deleted:
            exception.ActivityDeleted = True

        # Check if the user is already stickied into an activity
        if self.scheduled_activity.activity and self.scheduled_activity.activity.sticky:
            exception.Sticky = True

        if exception.messages() and not force:
            raise exception
        else:
            block = self.scheduled_activity.block
            self.delete()
            if settings.ENABLE_WAITLIST and self.scheduled_activity.waitlist.all().exists() and not block.locked and not dont_run_waitlist:
                if not self.scheduled_activity.is_full():
                    waitlists = EighthWaitlist.objects.get_next_waitlist(self.scheduled_activity)
                    self.scheduled_activity.notify_waitlist(waitlists, self.scheduled_activity)
            return "Successfully removed signup for {}.".format(block)

    def accept_pass(self):
        self.was_absent = False
        self.pass_accepted = True
        self.save(update_fields=["was_absent", "pass_accepted"])

    def reject_pass(self):
        self.was_absent = True
        self.pass_accepted = True
        self.save(update_fields=["was_absent", "pass_accepted"])

    def in_clear_absence_period(self):
        """Is the block for this signup in the clear absence period?"""
        return self.scheduled_activity.block.in_clear_absence_period()

    def archive_remove_absence(self):
        if self.was_absent:
            self.was_absent = False
            self.archived_was_absent = True
            self.save(update_fields=["was_absent", "archived_was_absent"])

    def __str__(self):
        return "{}: {}".format(self.user, self.scheduled_activity)

    class Meta:
        unique_together = (("user", "scheduled_activity"),)


class EighthWaitlistManager(Manager):
    """Model manager for EighthWaitlist."""

    def get_next_waitlist(self, activity):
        return self.filter(scheduled_activity_id=activity.id).order_by('time')

    def check_for_prescence(self, activity, user):
        return self.filter(scheduled_activity_id=activity.id, user=user).exists()

    def position_in_waitlist(self, aid, uid):
        try:
            return self.filter(scheduled_activity_id=aid, time__lt=self.get(scheduled_activity_id=aid, user_id=uid).time).count() + 1
        except EighthWaitlist.DoesNotExist:
            return 0


class EighthWaitlist(AbstractBaseEighthModel):
    objects = EighthWaitlistManager()
    time = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=False, on_delete=set_historical_user)
    block = models.ForeignKey(EighthBlock, null=False, on_delete=models.CASCADE)
    scheduled_activity = models.ForeignKey(EighthScheduledActivity, related_name="eighthwaitlist_set", null=False, db_index=True,
                                           on_delete=models.CASCADE)

    def __str__(self):
        return "{}: {}".format(self.user, self.scheduled_activity)


class EighthActivitySimilarity(AbstractBaseEighthModel):
    count = models.IntegerField()
    weighted = models.FloatField()

    @property
    def _weighted(self):
        cap = self.activity_set.first().capacity() + self.activity_set.last().capacity()
        if cap == 0:
            cap = 100
        return self.count / cap

    def update_weighted(self):
        self.weighted = self._weighted
        self.save(update_fields=["weighted"])

    def __str__(self):
        act_set = self.activity_set.all()
        return "{} and {}: {}".format(act_set.first(), act_set.last(), self.count)
