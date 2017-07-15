# -*- coding: utf-8 -*-
import datetime
import logging
from itertools import chain

from django.conf import settings
from django.contrib.auth.models import Group as DjangoGroup
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from simple_history.models import HistoricalRecords
from django.db import models, transaction
from django.db.models import Manager, Q
from django.utils import formats

from . import exceptions as eighth_exceptions
from ..users.models import User
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

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    user = models.OneToOneField(User, null=True, blank=True, on_delete=set_historical_user)
    online_attendance = models.BooleanField(default=True)
    contracted_eighth = models.BooleanField(default=True)
    show_full_name = models.BooleanField(default=False)

    history = HistoricalRecords()

    class Meta:
        unique_together = (("first_name", "last_name", "user", "online_attendance"),)
        ordering = ("last_name", "first_name",)

    @property
    def name(self):
        if self.show_full_name and self.first_name:
            return self.last_name + ", " + self.first_name
        else:
            return self.last_name

    @property
    def to_be_assigned(self):
        return sum([x in self.name.lower() for x in ["to be assigned", "to be determined", "to be announced"]])

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

    history = HistoricalRecords()

    unique_together = (("name", "capacity"),)

    @classmethod
    def total_capacity_of_rooms(cls, rooms):
        capacity = 0
        for r in rooms:
            c = r.capacity
            if c == -1:
                return -1
            else:
                capacity += c
        return capacity

    @property
    def formatted_name(self):
        if self.name[0].isdigit():  # All rooms starting with an integer will be prefixed
            return "Rm. {}".format(self.name)
        if self.name.startswith('Room'):  # Some room names are prefixed with 'Room'; for consistency
            return "Rm. {}".format(self.name[5:])
        if self.name.startswith('Weyanoke'):
            return "Wey. {}".format(self.name[9:])
        return self.name

    @property
    def to_be_determined(self):
        return sum([x in self.name.lower() for x in ["to be assigned", "to be determined", "to be announced"]])

    def __str__(self):
        return "{} ({})".format(self.name, self.capacity)
        # return "{}".format(self.name)

    class Meta:
        ordering = ("name",)


class EighthActivityExcludeDeletedManager(models.Manager):

    def get_queryset(self):
        return (super(EighthActivityExcludeDeletedManager, self).get_queryset().exclude(deleted=True))


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

    users_allowed = models.ManyToManyField(User, related_name="restricted_activity_set", blank=True)
    groups_allowed = models.ManyToManyField(DjangoGroup, related_name="restricted_activity_set", blank=True)

    users_blacklisted = models.ManyToManyField(User, blank=True)

    freshmen_allowed = models.BooleanField(default=False)
    sophomores_allowed = models.BooleanField(default=False)
    juniors_allowed = models.BooleanField(default=False)
    seniors_allowed = models.BooleanField(default=False)

    wed_a = models.BooleanField("Meets Wednesday A", default=False)
    wed_b = models.BooleanField("Meets Wednesday B", default=False)
    fri_a = models.BooleanField("Meets Friday A", default=False)
    fri_b = models.BooleanField("Meets Friday B", default=False)

    admin_comments = models.CharField(max_length=1000, blank=True)

    favorites = models.ManyToManyField(User, related_name="favorited_activity_set", blank=True)

    deleted = models.BooleanField(blank=True, default=False)

    history = HistoricalRecords()

    def capacity(self):
        # Note that this is the default capacity if the
        # rooms/capacity are not overridden for a particular block.
        if self.default_capacity:
            return self.default_capacity
        else:
            rooms = self.rooms.all()
            return EighthRoom.total_capacity_of_rooms(rooms)

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
        if include_restricted and self.restricted:
            name += " (R)"
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
        used = set([row[0] for row in EighthActivity.objects.values_list("id")])
        avail = nums - used
        return list(avail)

    def change_id_to(self, new_id):
        """Changes the internal ID field.

        Possible solution: https://djangosnippets.org/snippets/2691/

        """
        # EighthActivity.objects.filter(pk=self.pk).update(id=new_id)
        pass

    def get_active_schedulings(self):
        """Return EighthScheduledActivity's of this activity since the beginning of the year."""
        blocks = EighthBlock.objects.get_blocks_this_year()
        scheduled_activities = EighthScheduledActivity.objects.filter(activity=self)
        scheduled_activities = scheduled_activities.filter(block__in=blocks)

        return scheduled_activities

    @property
    def is_active(self):
        """Return whether an activity is "active." An activity is considered to be active if it has
        been scheduled at all this year."""
        scheduled_activities = self.get_active_schedulings()
        return scheduled_activities and scheduled_activities.count() > 0

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
            return []

        next_blocks = EighthBlock.objects.filter(date=next_block.date)
        return next_blocks

    def get_current_blocks(self):
        try:
            first_upcoming_block = self.get_first_upcoming_block()
            if first_upcoming_block is None:
                raise EighthBlock.DoesNotExist()
            block = (self.prefetch_related("eighthscheduledactivity_set").get(id=first_upcoming_block.id))
        except EighthBlock.DoesNotExist:
            return []

        return block.get_surrounding_blocks()

    def get_blocks_this_year(self):
        """Get a list of blocks that occur this school year."""

        date_start, date_end = get_date_range_this_year()

        return EighthBlock.objects.filter(date__gte=date_start, date__lte=date_end)


class EighthBlock(AbstractBaseEighthModel):
    """Represents an eighth period block.

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

    def save(self, *args, **kwargs):
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
            return reversed(blocks)
        return reversed(blocks[:quantity])

    def get_surrounding_blocks(self):
        """Get the blocks around the one given.

        Returns: a list of all of those blocks.

        """

        next = self.next_blocks()
        prev = self.previous_blocks()

        surrounding_blocks = list(chain(prev, [self], next))
        return surrounding_blocks

    def is_today(self):
        """Does the block occur today?"""
        return datetime.date.today() == self.date

    def signup_time_future(self):
        """Is the signup time in the future?"""
        now = datetime.datetime.now()
        return (now.date() < self.date or (self.date == now.date() and self.signup_time > now.time()))

    def date_in_past(self):
        """Is the block's date in the past?

        (Has it not yet happened?)

        """
        now = datetime.datetime.now()
        return (now.date() > self.date)

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
        return EighthSignup.objects.filter(scheduled_activity__block=self, user__in=User.objects.get_students()).count()

    def num_no_signups(self):
        """How many people have not signed up?"""
        signup_users_count = User.objects.get_students().count()
        return signup_users_count - self.num_signups()

    def get_unsigned_students(self):
        """Return a list of Users who haven't signed up for an activity."""
        return User.objects.get_students().exclude(eighthsignup__scheduled_activity__block=self)

    def get_hidden_signups(self):
        """ Return a list of Users who are *not* in the All Students list but have signed up for an activity.
            This is usually a list of signups for z-Withdrawn from TJ """
        return EighthSignup.objects.filter(scheduled_activity__block=self).exclude(user__in=User.objects.get_students())

    @property
    def letter_width(self):
        return (len(self.block_letter) - 1) * 6 + 15

    @property
    def letter_text(self):
        if any(char.isdigit() for char in self.block_letter):
            return "Block {}".format(self.block_letter)
        else:
            return "{} Block".format(self.block_letter)

    @property
    def short_text(self):
        """Display the date and block letter (mm/dd B, for example: '9/1 B')

        """
        return ("{} {}".format(self.date.strftime("%m/%d"), self.block_letter))

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
    """Represents the relationship between an activity and a block in which it has been scheduled.

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
    members = models.ManyToManyField(User, through="EighthSignup", related_name="eighthscheduledactivity_set")
    waitlist = models.ManyToManyField(User, through="EighthWaitlist", related_name="%(class)s_scheduledactivity_set")

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
        r = self.rooms.all()
        if r:
            return r
        return self.activity.rooms.all()

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
        name_with_flags = self.activity._name_with_flags(True, self.title) + cancelled_str
        if self.special and not self.activity.special:
            name_with_flags = "Special: " + name_with_flags
        return name_with_flags

    def get_true_sponsors(self):
        """Get the sponsors for the scheduled activity, taking into account activity defaults and
        overrides."""

        sponsors = self.sponsors.all()
        if len(sponsors) > 0:
            return sponsors
        else:
            return self.activity.sponsors.all()

    def user_is_sponsor(self, user):
        """Return whether the given user is a sponsor of the activity.

        Returns:
            Boolean

        """
        sponsors = self.get_true_sponsors()
        for sponsor in sponsors:
            sp_user = sponsor.user
            if sp_user == user:
                return True

        return False

    def get_true_rooms(self):
        """Get the rooms for the scheduled activity, taking into account activity defaults and
        overrides."""

        rooms = self.rooms.all()
        if len(rooms) > 0:
            return rooms
        else:
            return self.activity.rooms.all()

    def get_true_capacity(self):
        """Get the capacity for the scheduled activity, taking into account activity defaults and
        overrides."""

        c = self.capacity
        if c is not None:
            return c
        else:
            if self.rooms.count() == 0 and self.activity.default_capacity:
                # use activity-level override
                return self.activity.default_capacity

            rooms = self.get_true_rooms()
            return EighthRoom.total_capacity_of_rooms(rooms)

    def is_both_blocks(self):
        if self.both_blocks:
            return self.both_blocks
        else:
            return self.activity.both_blocks

    def get_restricted(self):
        """Get whether this scheduled activity is restricted."""
        if self.restricted:
            return self.restricted
        else:
            return self.activity.restricted

    def get_sticky(self):
        """Get whether this scheduled activity is sticky."""
        if self.sticky:
            return self.sticky
        else:
            return self.activity.sticky

    def get_finance(self):
        """Get whether this activity has an account with the finance office."""
        return self.activity.finance

    def get_administrative(self):
        """Get whether this scheduled activity is administrative."""
        if self.administrative:
            return self.administrative
        else:
            return self.activity.administrative

    def get_special(self):
        """Get whether this scheduled activity is special, checking the
           activity-level special settings.

        """
        if self.special:
            return self.special
        else:
            return self.activity.special

    def is_full(self):
        """Return whether the activity is full."""
        capacity = self.get_true_capacity()
        if capacity != -1:
            num_signed_up = self.eighthsignup_set.count()
            return num_signed_up >= capacity
        return False

    def is_almost_full(self):
        """Return whether the activity is almost full (>90%)."""
        capacity = self.get_true_capacity()
        if capacity != -1:
            num_signed_up = self.eighthsignup_set.count()
            return num_signed_up >= (0.9 * capacity)
        return False

    def is_overbooked(self):
        """Return whether the activity is overbooked."""
        capacity = self.get_true_capacity()
        if capacity != -1:
            num_signed_up = self.eighthsignup_set.count()
            return num_signed_up > capacity
        return False

    def is_too_early_to_signup(self, now=None):
        """Return whether it is too early to sign up for the activity if it is a presign (48 hour
        logic is here)."""
        if now is None:
            now = datetime.datetime.now()

        activity_date = (datetime.datetime.combine(self.block.date, datetime.time(0, 0, 0)))
        # Presign activities can only be signed up for 2 days in advance.
        presign_period = datetime.timedelta(days=2)

        return (now < (activity_date - presign_period))

    def has_open_passes(self):
        """Return whether there are passes that have not been acknowledged."""
        return self.eighthsignup_set.filter(after_deadline=True, pass_accepted=False)

    def get_viewable_members(self, user=None):
        """Get the list of members that you have permissions to view.

        Returns: List of members

        """
        members = []
        for member in self.members.all():
            show = False
            if member.dn and member.can_view_eighth:
                show = member.can_view_eighth

            if not show and user and user.is_eighth_admin:
                show = True
            if not show and user and user.is_teacher:
                show = True
            if not show and member == user:
                show = True

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
            show = False
            if member.dn and member.can_view_eighth:
                show = member.can_view_eighth

            if not show and user and user.is_eighth_admin:
                show = True
            if not show and user and user.is_teacher:
                show = True
            if not show and member == user:
                show = True

            if show:
                ids.append(member.id)

        return User.objects.filter(id__in=ids)

    def get_hidden_members(self, user=None):
        """Get the members that you do not have permission to view.

        Returns: List of members hidden based on their permission preferences

        """
        hidden_members = []
        for member in self.members.all():
            show = False
            if member.dn and member.can_view_eighth:
                show = member.can_view_eighth

            if not show and user and user.is_eighth_admin:
                show = True
            if not show and user and user.is_teacher:
                show = True
            if not show and member == user:
                show = True

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

        if self.block.block_letter and self.block.block_letter.upper() not in ["A", "B"]:
            # both_blocks is not currently implemented for blocks other than A and B
            return None

        other_instances = (EighthScheduledActivity.objects.filter(activity=self.activity, block__date=self.block.date))

        for inst in other_instances:
            if inst == self:
                continue

            if inst.block.block_letter in ["A", "B"]:
                return inst

        return False

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
        if not force:
            # Check if the user who sent the request has the permissions
            # to change the target user's signups
            if request is not None:
                if user != request.user and not request.user.is_eighth_admin:
                    exception.SignupForbidden = True

            # Check if the activity has been deleted
            if self.activity.deleted:
                exception.ActivityDeleted = True

            # Check if the user is already stickied into an activity
            in_stickie = (EighthSignup.objects.filter(user=user, scheduled_activity__activity__sticky=True,
                                                      scheduled_activity__block__in=all_blocks).exists())

            if not in_stickie:
                in_stickie = (EighthSignup.objects.filter(user=user, scheduled_activity__sticky=True,
                                                          scheduled_activity__block__in=all_blocks).exists())

            if in_stickie:
                exception.Sticky = True

            for sched_act in all_sched_act:
                # Check if the block has been locked
                if sched_act.block.locked:
                    exception.BlockLocked = True

                # Check if the scheduled activity has been cancelled
                if sched_act.cancelled:
                    exception.ScheduledActivityCancelled = True

                # Check if the activity is full
                if settings.ENABLE_WAITLIST and (add_to_waitlist or
                                                 (sched_act.is_full() and not self.is_both_blocks() and
                                                  (request is not None and not request.user.is_eighth_admin and request.user.is_student))):
                    if EighthWaitlist.objects.filter(user_id=user.id, block_id=self.block.id).exists():
                        EighthWaitlist.objects.filter(user_id=user.id, block_id=self.block.id).delete()
                    waitlist = EighthWaitlist.objects.create(user=user, block=self.block, scheduled_activity=sched_act)
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

        if force:
            EighthWaitlist.objects.filter(scheduled_activity_id=self.id, user_id=user.id, block_id=self.block.id).delete()

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
                        existing_blocks = [existing_signup.scheduled_activity.block,
                                           existing_signup.scheduled_activity.get_both_blocks_sibling().block]
                        logger.debug(existing_blocks)
                        EighthSignup.objects.filter(user=user, scheduled_activity__block__in=existing_blocks).delete()
                        EighthSignup.objects.create_signup(user=user, scheduled_activity=self, after_deadline=after_deadline,
                                                           previous_activity_name=previous_activity_name,
                                                           previous_activity_sponsors=previous_activity_sponsors, own_signup=(user == request.user))
                    if settings.ENABLE_WAITLIST and (previous_activity.waitlist.all().exists() and not self.block.locked and request is not None and
                                                     not request.session.get("disable_waitlist_transactions", False)):
                        if not previous_activity.is_full():
                            next_wait = EighthWaitlist.objects.get_next_waitlist(previous_activity)
                            try:
                                previous_activity.add_user(next_wait.user)
                                next_wait.delete()
                            except eighth_exceptions.SignupException:
                                pass

                except EighthSignup.DoesNotExist:
                    EighthSignup.objects.create_signup(user=user, scheduled_activity=self, after_deadline=after_deadline)
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

        logger.debug("Running cancel hooks: {}".format(self))

        if not self.cancelled:
            logger.debug("Cancelling {}".format(self))
            self.cancelled = True
        self.save()
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
            logger.debug("Uncancelling {}".format(self))
            self.cancelled = False
        self.save()
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

    def save(self, *args, **kwargs):
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
        if EighthSignup.objects.filter(user=user, scheduled_activity__block=scheduled_activity.block).count() > 0:
            raise ValidationError("EighthSignup already exists for this user on this block.")
        self.create(user=user, scheduled_activity=scheduled_activity, **kwargs)

    def get_absences(self):
        return (EighthSignup.objects.filter(was_absent=True, scheduled_activity__attendance_taken=True))


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

    user = models.ForeignKey(User, null=False, on_delete=set_historical_user)
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

    def save(self, *args, **kwargs):
        if self.has_conflict():
            raise ValidationError("EighthSignup already exists for this user on this block.")
        super(EighthSignup, self).save(*args, **kwargs)

    own_signup = models.BooleanField(default=False)

    history = HistoricalRecords()

    def validate_unique(self, *args, **kwargs):
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

        if len(exception.messages()) > 0 and not force:
            raise exception
        else:
            block = self.scheduled_activity.block
            self.delete()
            if settings.ENABLE_WAITLIST and self.scheduled_activity.waitlist.all().exists() and not block.locked and not dont_run_waitlist:
                if not self.scheduled_activity.is_full():
                    next_wait = EighthWaitlist.objects.get_next_waitlist(self.scheduled_activity)
                    self.scheduled_activity.add_user(next_wait.user)
                    next_wait.delete()
            return "Successfully removed signup for {}.".format(block)

    def accept_pass(self):
        self.was_absent = False
        self.present = True
        self.pass_accepted = True
        self.save()

    def reject_pass(self):
        self.was_absent = True
        self.pass_accepted = True
        self.save()

    def in_clear_absence_period(self):
        """Is the block for this signup in the clear absence period?"""
        return self.scheduled_activity.block.in_clear_absence_period()

    def archive_user_deleted(self):
        sa = self.scheduled_activity
        if sa.archived_member_count:
            sa.archived_member_count += 1
        else:
            sa.archived_member_count = 1
        sa.save()

    def archive_remove_absence(self):
        if self.was_absent:
            self.was_absent = False
            self.archived_was_absent = True
            self.save()

    def __str__(self):
        return "{}: {}".format(self.user, self.scheduled_activity)

    class Meta:
        unique_together = (("user", "scheduled_activity"),)


class EighthWaitlistManager(Manager):
    """Model manager for EighthWaitlist."""

    def get_next_waitlist(self, activity):
        return self.filter(scheduled_activity_id=activity.id).order_by('time').first()

    def position_in_waitlist(self, aid, uid):
        try:
            return self.filter(scheduled_activity_id=aid, time__lt=self.get(scheduled_activity_id=aid, user_id=uid).time).count() + 1
        except EighthWaitlist.DoesNotExist:
            return 0


class EighthWaitlist(AbstractBaseEighthModel):
    objects = EighthWaitlistManager()
    time = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, null=False, on_delete=set_historical_user)
    block = models.ForeignKey(EighthBlock, null=False, on_delete=models.CASCADE)
    scheduled_activity = models.ForeignKey(EighthScheduledActivity, related_name="eighthwaitlist_set", null=False, db_index=True,
                                           on_delete=models.CASCADE)

    def __str__(self):
        return "{}: {}".format(self.user, self.scheduled_activity)
