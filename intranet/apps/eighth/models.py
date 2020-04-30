# pylint: disable=too-many-lines; Allow more than 1000 lines
import datetime
import logging
import string
from typing import Collection, Iterable, List, Optional, Union

from cacheops import invalidate_obj
from sentry_sdk import add_breadcrumb, capture_exception
from simple_history.models import HistoricalRecords

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group as DjangoGroup
from django.core import validators
from django.core.cache import cache
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.db import models, transaction
from django.db.models import Count, Manager, Q, QuerySet
from django.http.request import HttpRequest
from django.utils import formats, timezone

from ...utils.date import get_date_range_this_year, is_current_year
from ...utils.deletion import set_historical_user
from ...utils.locking import lock_on
from ..notifications.tasks import email_send_task
from . import exceptions as eighth_exceptions

logger = logging.getLogger(__name__)


class AbstractBaseEighthModel(models.Model):
    """ Abstract base model that includes created
        and last modified times.

        Attributes:
            created_time (datetime): The time the model was created
            last_modified_time (datetime): The time the model was
                last modified.
    """

    created_time = models.DateTimeField(auto_now_add=True, null=True)
    last_modified_time = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        abstract = True


class EighthSponsor(AbstractBaseEighthModel):
    """ Represents a sponsor for an eighth period activity.

    A sponsor could be linked to an actual user or just a name.

    Attributes:
        first_name (str): The first name of the sponsor.
        last_name (str): The last name of the sponsor.
        user (User): A :class:`users.User` object linked
            to the sponsor.
        department (str): The sponsor's department.
        full_time (bool): Whether the sponsor is full-time.
        online_attendance (bool): Whether the sponsor takes.
            attendance online.
        contracted_eighth (bool): Whether the sponsor is
            contracted to supervise 8th periods.
        show_full_name (bool): Whether to always show the sponsor's full name
            (e.x. because there are two teachers named Lewis).
    """

    # Hard-coded list of departments in the school
    DEPARTMENTS = (
        ("general", "General"),
        ("math_cs", "Math/CS"),
        ("english", "English"),
        ("social_studies", "Social Studies"),
        ("fine_arts", "Fine Arts"),
        ("health_pe", "Health/PE"),
        ("scitech", "Science/Technology"),
    )

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
        unique_together = (("first_name", "last_name", "user", "online_attendance", "full_time", "department"),)
        ordering = ("last_name", "first_name")

    @property
    def name(self) -> str:
        """If show_full_name is set, returns "last name, first name". Otherwise, returns last name only.

        Returns:
            The name to display for the sponsor, omitting the first name unless explicitly requested.

        """
        if self.show_full_name and self.first_name:
            return self.last_name + ", " + self.first_name
        else:
            return self.last_name

    @property
    def to_be_assigned(self) -> bool:
        """Returns True if the sponsor's name contains "to be assigned" or similar.

        Returns:
            Whether the sponsor is a "to be assigned" sponsor.

        """
        return any(x in self.name.lower() for x in ["to be assigned", "to be determined", "to be announced"])

    def __str__(self):
        return self.name


class EighthRoom(AbstractBaseEighthModel):
    """ Represents a room in which an eighth period activity can be held.

    Attributes:
        name (str): The name of the room.
        capacity (int): The maximum capacity of the room (-1 for unlimited, 0 to prevent student signup)
        available_for_eighth (bool): Whehther the room is available for eighth period signups.

    """

    name = models.CharField(max_length=100)
    capacity = models.SmallIntegerField(default=28)
    available_for_eighth = models.BooleanField(default=True)

    history = HistoricalRecords()

    unique_together = (("name", "capacity"),)

    @staticmethod
    def total_capacity_of_rooms(rooms: Iterable["EighthRoom"]) -> int:
        """ Returns the total capacity of the provided rooms.

        Args:
            rooms: Rooms to determine total capacity for.

        Returns:
            The total capacity of the provided rooms.

        """

        capacity = 0
        for r in rooms:
            if r.capacity == -1:
                return -1
            capacity += r.capacity
        return capacity

    @property
    def formatted_name(self) -> str:
        """The formatted name of the room.

        If it looks like the room is a numbered room -- the name starts with either a number or with
        the text "Room" -- returns "Rm. <room number>."

        Returns:
            The formatted name of the Room.

        """
        if self.name[0] in string.digits:
            # All rooms starting with an integer will be prefixed
            return "Rm. {}".format(self.name)
        if self.name.startswith("Room"):
            # Some room names are prefixed with 'Room'; for consistency
            return "Rm. {}".format(self.name[5:])
        return self.name

    @property
    def to_be_determined(self) -> bool:
        """Whether the Room needs to be assigned."""
        return any(x in self.name.lower() for x in ["to be assigned", "to be determined", "to be announced"])

    def __str__(self):
        return "{} ({})".format(self.name, self.capacity)

    class Meta:
        ordering = ("name",)


class EighthActivityExcludeDeletedManager(models.Manager):
    def get_queryset(self):
        return super(EighthActivityExcludeDeletedManager, self).get_queryset().exclude(deleted=True)


class EighthActivity(AbstractBaseEighthModel):
    """ Represents an eighth period activity.

    Attributes:
        name(str): The name of the activity, max length 100 characters.
        description (str): The description of the activity, shown on the signup page below
            the other information. Information on an EighthScheduledActivity basis can
            be found in the "comments" field of that model. Max length 2000 characters.
        sponsors (:obj:`list` of :obj:`EighthSponsor`): The default activity-level sponsors for the activity.
            On an EighthScheduledActivity basis, you should NOT query this field.
            Instead, use scheduled_activity.get_true_sponsors()
        rooms (:obj:`list` of :obj:`EighthRoom`): The default activity-level rooms for the activity.
            On an EighthScheduledActivity basis, you should NOT query this field.
            Use scheduled_activity.get_true_rooms()
        default_capacity (int): The default capacity, which overrides the sum of the default rooms when
            scheduling the activity. By default, this has a null value and is ignored.
        presign (bool): If True, the activity can only be signed up for within 48 hours of the day that
            the activity is scheduled.
        one_a_day (bool): If True, a student can only sign up for one instance of this activity per day.
        both_blocks (bool): If True, a signup for an EighthScheduledActivity during an A or B block will
            enforce and automatically trigger a signup on the other block. Does not enforce signups
            for blocks other than A and B.
        sticky (bool): If True, then students who sign up or are placed in this activity cannot switch out of it.
            A sticky activity should also be restricted, unless you're mean.
        special (bool): If True, then the activity receives a special designation on the signup list, and is stuck
            to the top of the list.
        administrative (bool): If True, then students cannot see the activity in their signup list. However,
            the activity still exists in the system and can be seen by administrators. Students can still
            sign up for the activity through the API -- this does not prevent students from signing up
            for it, and just merely hides it from view. An administrative activity should be restricted.
        finance (str): The account name of the club with the Finance Office. If blank or null, there is no account.
        restricted (str): Whether the signups for the activity are restricted to certain users/groups or if
            there are blacklisted users.
        users_allowed (:obj:`list` of :obj:`User`): Individual users allowed to sign up for this activity.
            Extensive use of this is discouraged; make a group instead through the
            "Add and Assign Empty Group" button on the Edit Activity page. Only takes effect if the activity
            is restricted.
        groups_allowed (:obj:`list` of :obj:`Group`): Individual groups allowed to sign up for this activity.
            Only takes effect if the activity is restricted.
        users_blacklisted (:obj:`list` of :obj:`User`): Individual users who are not allowed to sign up for
            this activity. Only takes effect if the activity is not restricted.
        freshman_allowed (bool): Whether freshmen are allowed to sign up for this activity. Only
            takes effect if the activity is restricted.
        sophomores_allowed (bool): Whether sophomores are allowed to sign up for this activity. Only
            takes effect if the activity is restricted.
        juniors_allowed (bool): Whether juniors are allowed to sign up for this activity. Only
            takes effect if the activity is restricted.
        seniors_allowed (bool): Whether seniors are allowed to sign up for this activity. Only
            takes effect if the activity is restricted.
        wed_a (bool): Whether the activity generally meets on Wednesday A blocks. Does not affect schedule, is just information for the Eighth Office.
        wed_b (bool): Whether the activity generally meets on Wednesday B blocks. Does not affect schedule, is just information for the Eighth Office.
        fri_a (bool): Whether the activity generally meets on Friday A blocks. Does not affect schedule, is just information for the Eighth Office.
        fri_b (bool): Whether the activity generally meets on Friday B blocks. Does not affect schedule, is just information for the Eighth Office.
        admin_comments (str): Notes for the Eighth Office.
        favorites (:obj:`list` of :obj:`User`): A ManyToManyField of User objects who have favorited the activity.
        similarities (:obj:`list` of :obj:`EighthActivitySimilarity`): A ManyToManyField of EighthActivitySimilarity
            objects which are similar to this activity.
        deleted (bool): Whether the activity still technically exists in the system, but was marked to be deleted.

    """

    objects = models.Manager()
    undeleted_objects = EighthActivityExcludeDeletedManager()

    name = models.CharField(max_length=100, validators=[validators.MinLengthValidator(4)])  # This should really be unique
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

    similarities = models.ManyToManyField("EighthActivitySimilarity", related_name="activity_set", blank=True)

    deleted = models.BooleanField(blank=True, default=False)

    history = HistoricalRecords()

    def capacity(self) -> int:
        """Returns 'default_capacity' if it is set. Otherwise, returns the total capacity of all the activity's rooms.

        Returns:
            The activity's capacity.

        """
        # Note that this is the default capacity if the
        # rooms/capacity are not overridden for a particular block.
        return self.default_capacity or EighthRoom.total_capacity_of_rooms(self.rooms.all())

    @property
    def aid(self) -> int:
        """The publicly visible activity ID.

        Returns:
            The public activity ID.

        """
        return self.id

    @property
    def name_with_flags(self) -> str:
        """Return the activity name with special, both blocks, restricted, administrative, sticky,
        and deleted flags.

        Returns:
            The activity name with all flags.

        """
        return self._name_with_flags(True)

    @property
    def name_with_flags_no_restricted(self) -> str:
        """Returns the activity's name with flags.
       These flags indicate whether the activity is special, both blocks, administrative, sticky, and/or cancelled.

        Returns:
            The activity name with all flags except the "restricted" flag.

        """
        return self._name_with_flags(False)

    def _name_with_flags(self, include_restricted: bool, title: Optional[str] = None) -> str:
        """Generates the activity's name with flags.

        Args:
            include_restricted: Whether to include the "restricted" flag.
            title: An optional title to add after the activity name (but before the flags)

        Returns:
            The activity name with all the appropriate flags.

        """
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
    def restricted_activities_available_to_user(cls, user: "get_user_model()") -> List[int]:
        """Finds the restricted activities available to the given user.

        Args:
            user: The User to find the restricted activities for.

        Returns:
            The restricted activities available to the user.

        """
        if not user:
            return []

        q = Q(users_allowed=user.id) | Q(groups_allowed__user=user.id)

        if user and user.grade and user.grade.number and user.grade.name and 9 <= user.grade.number <= 12:
            q |= Q(**{"{}_allowed".format(user.grade.name_plural): True})

        return EighthActivity.objects.filter(q).values_list("id", flat=True)

    @classmethod
    def available_ids(cls) -> List[int]:
        """Returns all available IDs not used by an EighthActivity.

        Returns:
            A list of the available activity IDs.

        """
        id_min = 1
        id_max = 3200
        nums = set(range(id_min, id_max))
        used = {row[0] for row in EighthActivity.objects.values_list("id")}
        avail = nums - used
        return list(avail)

    def get_active_schedulings(self) -> Union[QuerySet, Collection["EighthScheduledActivity"]]:  # pylint: disable=unsubscriptable-object
        """Returns all EighthScheduledActivitys scheduled this year for this activity.

        Returns:
            EighthScheduledActivitys of this activity occurring this year.

        """
        date_start, date_end = get_date_range_this_year()

        return EighthScheduledActivity.objects.filter(activity=self, block__date__gte=date_start, block__date__lte=date_end)

    @property
    def is_active(self) -> bool:
        """Returns whether an activity is "active."
 An activity is considered to be active if it has been scheduled at all this year.
        Returns:
            Whether the activity is active.

        """
        return self.get_active_schedulings().exists()

    @property
    def frequent_users(self) -> Union[QuerySet, Collection["get_user_model()"]]:  # pylint: disable=unsubscriptable-object
        """Return a QuerySet of user id's and counts that have signed up for this activity more than
        `settings.SIMILAR_THRESHOLD` times.

        This is used for suggesting activities to users.

        Returns:
            A QuerySet of users who attend this activity frequently.

        """
        key = "eighthactivity_{}:frequent_users".format(self.id)
        cached = cache.get(key)
        if cached:
            return cached
        freq_users = (
            self.eighthscheduledactivity_set.exclude(Q(eighthsignup_set__user=None) | Q(administrative=True) | Q(special=True) | Q(restricted=True))
            .values("eighthsignup_set__user")
            .annotate(count=Count("eighthsignup_set__user"))
            .filter(count__gte=settings.SIMILAR_THRESHOLD)
            .order_by("-count")
        )
        cache.set(key, freq_users, timeout=60 * 60 * 24 * 7)
        return freq_users

    @property
    def is_popular(self) -> bool:
        """Returns whether this activity has more than ``settings.SIMILAR_THRESHOLD * 2`` frequent_users.

        Returns:
            Whether this activity has more than ``settings.SIMILAR_THRESHOLD * 2`` frequent_users.

        """
        return self.frequent_users.count() > (settings.SIMILAR_THRESHOLD * 2)

    class Meta:
        verbose_name_plural = "eighth activities"

    def __str__(self):
        return self.name_with_flags


class EighthBlockQuerySet(models.query.QuerySet):
    def this_year(self) -> Union[QuerySet, Collection["EighthBlock"]]:  # pylint: disable=unsubscriptable-object
        """Get EighthBlocks from this school year only.

        Returns:
            A QuerySet containing all of the blocks selected by this QuerySet that occur during this school year.

        """
        start_date, end_date = get_date_range_this_year()
        return self.filter(date__gte=start_date, date__lte=end_date)

    def filter_today(self) -> Union[QuerySet, Collection["EighthBlock"]]:  # pylint: disable=unsubscriptable-object
        """Gets EighthBlocks that occur today.

        Returns:
            A QuerySet containing all of the blocks selected by this QuerySet that occur today.

        """
        return self.filter(date=timezone.localdate())


class EighthBlockManager(models.Manager):
    def get_queryset(self):
        return EighthBlockQuerySet(self.model, using=self._db)

    def get_upcoming_blocks(self, max_number: int = -1) -> Union[QuerySet, Collection["EighthBlock"]]:  # pylint: disable=unsubscriptable-object
        """Gets the given number of upcoming blocks that will take place in the future.

        If there is no block in the future, the most recent block will be returned.

        Returns:
            A QuerySet of the X upcoming ``EighthBlock`` objects.

        """

        now = timezone.localtime()

        # Show same day if it's before 17:00
        if now.hour < 17:
            now = now.replace(hour=0, minute=0, second=0, microsecond=0)

        blocks = self.order_by("date", "block_letter").filter(date__gte=now)

        if max_number == -1:
            return blocks

        return blocks[:max_number]

    def get_first_upcoming_block(self) -> "EighthBlock":
        """Gets the first upcoming block (the first block that will take place in the future).

        Returns:
            The first upcoming ``EighthBlock`` object, or ``None`` if there are none upcoming.

        """

        return self.get_upcoming_blocks().first()

    def get_next_upcoming_blocks(self) -> Union[QuerySet, Collection["EighthBlock"]]:  # pylint: disable=unsubscriptable-object
        """Gets the next upccoming blocks.

        It finds the other blocks that are occurring on the day of the
        first upcoming block.

        Returns:
            A QuerySet of the next upcoming ``EighthBlock`` objects.

        """

        next_block = EighthBlock.objects.get_first_upcoming_block()

        if not next_block:
            return EighthBlock.objects.none()

        next_blocks = EighthBlock.objects.filter(date=next_block.date)
        return next_blocks

    def get_blocks_this_year(self) -> Union[QuerySet, Collection["EighthBlock"]]:  # pylint: disable=unsubscriptable-object
        """Gets a QuerySet of blocks that occur this school year.

        Returns:
            A QuerySet of all the blocks that occur during this school year.

        """

        date_start, date_end = get_date_range_this_year()

        return EighthBlock.objects.filter(date__gte=date_start, date__lte=date_end)

    def get_blocks_today(self) -> Union[QuerySet, Collection["EighthBlock"]]:  # pylint: disable=unsubscriptable-object
        """Gets a QuerySet of blocks that occur today.

        Returns:
            A QuerySet of all the blocks that occur today.

        """
        return self.filter(date=timezone.localdate())


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

    def save(self, *args, **kwargs):  # pylint: disable=signature-differs
        """Capitalize the first letter of the block name."""
        letter = getattr(self, "block_letter", None)
        if letter and len(letter) >= 1:
            self.block_letter = letter[:1].upper() + letter[1:]

        super(EighthBlock, self).save(*args, **kwargs)

    def next_blocks(self, quantity: int = -1) -> Union[QuerySet, Collection["EighthBlock"]]:  # pylint: disable=unsubscriptable-object
        """Gets future blocks this school year in order.

        Args:
            quantity: The number of blocks to list after this block, or -1 for all following blocks.

        Returns:
            A QuerySet with the specified number of future blocks this school year.
            If ``quantity`` is passed, then the QuerySet will not be filter()-able.

        """
        blocks = (
            EighthBlock.objects.get_blocks_this_year()
            .order_by("date", "block_letter")
            .filter(Q(date__gt=self.date) | (Q(date=self.date) & Q(block_letter__gt=self.block_letter)))
        )
        if quantity == -1:
            return blocks
        return blocks[:quantity]

    def previous_blocks(self, quantity: int = -1) -> Union[QuerySet, Collection["EighthBlock"]]:  # pylint: disable=unsubscriptable-object
        """Gets the previous blocks this school year in order.

        Args:
            quantity: The number of blocks to list before this block, or -1 for all previous blocks.

        Returns:
            If `quantity` is not passed, retuns a QuerySet with all the blocks this school year
            before this block.

            If `quantity` is passed, returns a list with the specified number of blocks this
            school year before this block.

        """
        blocks = (
            EighthBlock.objects.get_blocks_this_year()
            .order_by("-date", "-block_letter")
            .filter(Q(date__lt=self.date) | (Q(date=self.date) & Q(block_letter__lt=self.block_letter)))
        )
        if quantity == -1:
            return blocks.reverse()
        return blocks[:quantity:-1]

    def is_today(self) -> bool:
        """Returns whether the block occurs today.

        Returns:
            Whether the block occurs today.

        """
        return timezone.localdate() == self.date

    def signup_time_future(self) -> bool:
        """Returns whether the block closes in the future.

        Returns:
            Whether the block's signup time is in the future.

        """
        now = timezone.localtime()
        return now.date() < self.date or (self.date == now.date() and self.signup_time > now.time())

    def date_in_past(self) -> bool:
        """Returns whether the block has already happened.

        Returns:
            Whether the block's date is in the past.

        """
        return timezone.localdate() > self.date

    def in_clear_absence_period(self) -> bool:
        """Returns whether today's date  is within the block's clear absence period.
        This determines whether the option to clear an eighth period absence should be shown.
        If the block is not within the clear absence period, an absence cannot be cleared.

        Returns:
            Whether the current date is in the block's clear absence period.

        """
        now = timezone.localtime()
        two_weeks = self.date + datetime.timedelta(days=settings.CLEAR_ABSENCE_DAYS)
        return now.date() <= two_weeks

    def attendance_locked(self) -> bool:
        """Returns whether the block's attendance is locked.

        If the block's attendance is locked, non-eighth admins cannot
        change attendance.

        Returns:
            Whether the block's attendance is locked.

        """
        now = timezone.localtime()
        return now.date() > self.date or (now.date() == self.date and now.time() > datetime.time(settings.ATTENDANCE_LOCK_HOUR, 0))

    def num_signups(self) -> int:
        """Gets how many people have signed up for
        an activity this block.

        Returns:
            The number of people who have signed up for an activity during this block.

        """
        return EighthSignup.objects.filter(scheduled_activity__block=self, user__in=get_user_model().objects.get_students()).count()

    def num_no_signups(self) -> int:
        """Gets how many people have not signed up
        for an activity this block.

        Returns:
            The number of people who have not signed up for an activity during this block.

        """
        signup_users_count = get_user_model().objects.get_students().count()
        return signup_users_count - self.num_signups()

    def get_unsigned_students(self) -> Union[QuerySet, Collection["get_user_model()"]]:  # pylint: disable=unsubscriptable-object
        """Return a QuerySet of people who haven't signed up for an
        activity during this block.

        Returns:
            The users who have not signed up for an activity during this block.

        """
        return get_user_model().objects.get_students().exclude(eighthsignup__scheduled_activity__block=self)

    def get_hidden_signups(self) -> Union[QuerySet, Collection["EighthSignup"]]:  # pylint: disable=unsubscriptable-object
        """Returns a QuerySet of EighthSignups whose users are not students
        but have signed up for an activity.

        This is usually a list of signups for the z-Withdrawn from TJ activity.

        Returns:
            A QuerySet of users who are not current students but have signed up for an activity this block.

        """
        return EighthSignup.objects.filter(scheduled_activity__block=self).exclude(user__in=get_user_model().objects.get_students())

    @property
    def letter_width(self) -> int:
        """Returns the width in pixels that should be allocated for the block_letter on the signup page.

        Return:
            The width in pixels of the block letter.

        """
        return (len(self.block_letter) - 1) * 6 + 15

    @property
    def short_text(self) -> str:
        """Returns the date and block letter for this block.

         It is returned in the format of  MM/DD B, like "9/1 B"

        Returns:
            The date and block letter.

        """
        return "{} {}".format(self.date.strftime("%m/%d"), self.block_letter)

    @property
    def is_this_year(self) -> bool:
        """Return whether the block occurs during this school year.

        Returns:
            Whether the block occurs during this school year.

        """
        return is_current_year(datetime.datetime.combine(self.date, datetime.time()))

    @property
    def formatted_date(self) -> str:
        """Returns the block date, formatted according to ``settings.EIGHTH_BLOCK_DATE_FORMAT``.

        Returns:
            The formatted block date.

        """
        return formats.date_format(self.date, settings.EIGHTH_BLOCK_DATE_FORMAT)

    def __str__(self):
        return "{} ({})".format(self.formatted_date, self.block_letter)

    class Meta:
        unique_together = (("date", "block_letter"),)
        ordering = ("date", "block_letter")


class EighthScheduledActivityManager(Manager):
    """Model Manager for EighthScheduledActivity."""

    def for_sponsor(
        self, sponsor: EighthSponsor, include_cancelled: bool = False
    ) -> Union[QuerySet, Collection["EighthScheduledActivity"]]:  # pylint: disable=unsubscriptable-object
        """Returns a QuerySet of EighthScheduledActivities where the given EighthSponsor is
        sponsoring.

        If a sponsorship is defined in an EighthActivity, it may be overridden
        on a block by block basis in an EighthScheduledActivity. Sponsors from
        the EighthActivity do not carry over.

        EighthScheduledActivities that are deleted or cancelled are also not
        counted.

        Args:
            sponsor: The sponsor to search for.
            include_cancelled: Whether to include cancelled activities. Deleted
                activities are always excluded.

        Returns:
            A QuerySet of EighthScheduledActivities where the given EighthSponsor
                is sponsoring.

        """
        sponsoring_filter = Q(sponsors=sponsor) | (Q(sponsors=None) & Q(activity__sponsors=sponsor))
        sched_acts = EighthScheduledActivity.objects.exclude(activity__deleted=True).filter(sponsoring_filter).distinct()
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

    def get_all_associated_rooms(self) -> Union[QuerySet, Collection["EighthRoom"]]:  # pylint: disable=unsubscriptable-object
        """Returns a QuerySet of all the rooms associated with either this EighthScheduledActivity or its EighthActivity.

        Returns:
            A QuerySet of all the rooms associated with either this EighthScheduledActivity or its EighthActivity.

        """
        return (self.rooms.all() | self.activity.rooms.all()).distinct()

    @property
    def full_title(self) -> str:
        """Gets the full title for the activity, appending the title of the scheduled activity to
        the activity's name.

        Returns:
            The full title for the scheduled activity, without flags.

        """
        cancelled_str = " (Cancelled)" if self.cancelled else ""
        act_name = self.activity.name + cancelled_str
        if self.special and not self.activity.special:
            act_name = "Special: " + act_name
        return act_name if not self.title else "{} - {}".format(act_name, self.title)

    @property
    def title_with_flags(self) -> str:
        """Gets the title for the activity, appending the title of the
        scheduled activity to the activity's name and flags.

        Returns:
            The full title for the scheduled activity, with flags.

        """
        cancelled_str = " (Cancelled)" if self.cancelled else ""
        name_with_flags = self.activity._name_with_flags(True, self.title) + cancelled_str  # pylint: disable=protected-access
        if self.special and not self.activity.special:
            name_with_flags = "Special: " + name_with_flags
        return name_with_flags

    def get_true_sponsors(self) -> Union[QuerySet, Collection[EighthSponsor]]:  # pylint: disable=unsubscriptable-object
        """Retrieves the sponsors for the scheduled activity, taking into account activity defaults and
        overrides.

        Returns:
            The sponsors for this scheduled activity.

        """
        return self.sponsors.all() or self.activity.sponsors.all()

    def user_is_sponsor(self, user: "get_user_model()") -> bool:
        """Returns whether the given user is a sponsor of the activity.

        Args:
            user: The user to check for sponsorship of this activity.

        Returns:
            Whether the given user is a sponsor of the activity.

        """
        return self.get_true_sponsors().filter(user=user).exists()

    def get_true_rooms(self) -> Union[QuerySet, Collection[EighthRoom]]:  # pylint: disable=unsubscriptable-object
        """Retrieves the rooms for the scheduled activity, taking into account
        activity defaults and overrides.

        Returns:
            The true room list of the scheduled activity.

        """
        return self.rooms.all() or self.activity.rooms.all()

    def get_true_capacity(self) -> int:
        """Retrieves the capacity for the scheduled activity, taking into
        account activity defaults and overrides.

        Returns:
            The true capacity of the scheduled activity.

        """
        if self.capacity is not None:
            return self.capacity

        rooms = self.rooms.all()
        if rooms:
            return EighthRoom.total_capacity_of_rooms(rooms)

        if self.activity.default_capacity:
            # use activity-level override
            return self.activity.default_capacity

        return EighthRoom.total_capacity_of_rooms(self.activity.rooms.all())

    def is_both_blocks(self) -> bool:
        """Gets whether this scheduled activity runs both blocks.

        Returns:
            Whether this scheduled activity runs both blocks.

        """
        return self.both_blocks or self.activity.both_blocks

    def get_restricted(self) -> bool:
        """Gets whether this scheduled activity is restricted.

        Returns:
            Whether this scheduled activity is restricted.

        """
        return self.restricted or self.activity.restricted

    def get_sticky(self) -> bool:
        """Gets whether this scheduled activity is sticky.

        Returns:
            Whether this scheduled activity is sticky.

        """
        return self.sticky or self.activity.sticky

    def get_finance(self) -> str:
        """Retrieves the name of this activity's account with the
        finance office, if any.

        Returns:
            The name of this activity's account with the finance office.

        """
        return self.activity.finance

    def get_administrative(self) -> bool:
        """Returns whether this scheduled activity is administrative.

        Returns:
            Whether this activity is administrative

        """
        return self.administrative or self.activity.administrative

    def get_special(self) -> bool:
        """Returns whether this scheduled activity is special.

        Returns:
            Whether this scheduled activity is special.

        """
        return self.special or self.activity.special

    def is_full(self, nocache: bool = False) -> bool:
        """Returns whether the scheduled activity is full.

        Args:
            nocache: Whether to disable caching for the query that checks the scheduled activity's
                current capacity.

        Returns:
            Whether this scheduled activity is full.

        """
        capacity = self.get_true_capacity()  # We don't disable caching because this changes much less frequently

        signups = self.eighthsignup_set.all()
        if nocache:
            signups = signups.nocache()

        return capacity != -1 and signups.count() >= capacity

    def is_almost_full(self) -> bool:
        """Returns whether the scheduled activity is almost full (>=90%).

        Returns:
            Whether this scheduled activity is at least 90% full.

        """
        capacity = self.get_true_capacity()
        return capacity != -1 and self.eighthsignup_set.count() >= (0.9 * capacity)

    def is_overbooked(self) -> bool:
        """Returns whether the activity is overbooked (>100%) capacity.

        Returns:
            Whether this scheduled activity is overbooked.

        """
        capacity = self.get_true_capacity()
        return capacity != -1 and self.eighthsignup_set.count() > capacity

    def is_too_early_to_signup(self, now: Optional[datetime.datetime] = None) -> bool:
        """Returns whether it is too early to sign up for the activity
        if it is a presign.

        This contains the 48 hour presign logic.

        Args:
            now: A datetime object to use for the check instead of the current time.

        Returns:
            Whether it is too early to sign up for this scheduled activity.

        """
        if now is None:
            now = timezone.localtime()

        activity_date = datetime.datetime.combine(self.block.date, datetime.time(0, 0, 0))
        if now.tzinfo is not None:
            activity_date = timezone.make_aware(activity_date, now.tzinfo)
        # Presign activities can only be signed up for 2 days in advance.
        presign_period = datetime.timedelta(days=2)

        return now < (activity_date - presign_period)

    def has_open_passes(self) -> bool:
        """Returns whether there are passes that have not been acknowledged.

        Returns:
            Whether this activity has open passes.

        """
        return self.eighthsignup_set.filter(after_deadline=True, pass_accepted=False).exists()

    def _get_viewable_members(
        self, user: "get_user_model()"
    ) -> Union[QuerySet, Collection["get_user_model()"]]:  # pylint: disable=unsubscriptable-object
        """Get an unsorted QuerySet of the members that you have permission to view.

        Args:
            user: The user who is attempting to view the member list.

        Returns:
            Unsorted QuerySet of the members that you have permssion to view.

        """
        if user and (user.is_eighth_admin or user.is_eighthoffice or user.is_teacher):
            return self.members.all()
        else:
            q = Q(properties__parent_show_eighth=True, properties__self_show_eighth=True)
            if user:
                q |= Q(id=user.id)
            return self.members.filter(q)

    def get_viewable_members(
        self, user: "get_user_model()" = None
    ) -> Union[QuerySet, Collection["get_user_model()"]]:  # pylint: disable=unsubscriptable-object
        """Returns a QuerySet of the members that you have permission to view, sorted alphabetically.

        Args:
            user: The user who is attempting to view the member list.

        Returns:
            QuerySet of the members that you have permission to view, sorted alphabetically.

        """
        return self._get_viewable_members(user).order_by("last_name", "first_name")

    def get_viewable_members_serializer(self, request) -> Union[QuerySet, Collection["get_user_model()"]]:  # pylint: disable=unsubscriptable-object
        """Given a request, returns an unsorted QuerySet of the members that the requesting user
        has permission to view.

        Args:
            request: The request object associated with the member list query.

        Returns:
            Unsorted QuerySet of the members that you have permssion to view.

        """
        return self._get_viewable_members(request.user)

    def get_hidden_members(
        self, user: "get_user_model()" = None
    ) -> Union[QuerySet, Collection["get_user_model()"]]:  # pylint: disable=unsubscriptable-object
        """Returns a QuerySet of the members that you do not have permission to view.

        Args:
            user: The user who is attempting to view the member list.

        Returns:
            Unsorted QuerySet of the members that you do not have permission to view.

        """
        if user and (user.is_eighth_admin or user.is_eighthoffice or user.is_teacher):
            return get_user_model().objects.none()
        else:
            hidden_members = self.members.exclude(properties__parent_show_eighth=True, properties__self_show_eighth=True)
            if user:
                hidden_members = hidden_members.exclude(id=user.id)

            return hidden_members

    def get_both_blocks_sibling(self) -> Optional["EighthScheduledActivity"]:
        """If this is a both-blocks activity, get the other EighthScheduledActivity
        object that occurs on the other block.

        both_blocks means A and B block, NOT all of the blocks on that day.

        Returns:
            EighthScheduledActivity object if found.
            ``None``, if the activity cannot have a sibling.

        """
        if not self.is_both_blocks():
            return None

        if self.block.block_letter not in ["A", "B"]:
            # both_blocks is not currently implemented for blocks other than A and B
            return None

        other_block_letter = "A" if self.block.block_letter == "B" else "B"

        try:
            return EighthScheduledActivity.objects.exclude(pk=self.pk).get(
                activity=self.activity, block__date=self.block.date, block__block_letter=other_block_letter
            )
        except EighthScheduledActivity.DoesNotExist:
            return None

    def notify_waitlist(self, waitlists: Iterable["EighthWaitlist"]):
        """Notifies all users on the given EighthWaitlist objects that the activity they are on the waitlist for has an open spot.

        Args:
            waitlists: The EighthWaitlist objects whose users should be notified that the activity has an open slot.

        """
        for waitlist in waitlists:
            email_send_task.delay(
                "eighth/emails/waitlist.txt",
                "eighth/emails/waitlist.html",
                {"activity": waitlist.scheduled_activity},
                "Open Spot Notification",
                [waitlist.user.primary_email_address],
            )

    @transaction.atomic  # This MUST be run in a transaction. Do NOT remove this decorator.
    def add_user(
        self,
        user: "get_user_model()",
        request: Optional[HttpRequest] = None,
        force: bool = False,
        no_after_deadline: bool = False,
        add_to_waitlist: bool = False,
    ):
        """Signs up a user to this scheduled activity if possible. This is where the magic happens.

        Raises an exception if there's a problem signing the user up
        unless the signup is forced and the requesting user has permission.

        Args:
            user: The user to add to the scheduled activity.
            request: The request object associated with the signup action. Should always be passed if applicable,
                as some information is extracted from the request.
            force: Whether to force the signup.
            no_after_deadline: Whether to mark the user as not having signed up after the deadline, regardless of
                whether they did or not.
            add_to_waitlist: Explicitly add the user to the waitlist.

        """
        if request is not None:
            force = (force or ("force" in request.GET)) and request.user.is_eighth_admin
            add_to_waitlist = (add_to_waitlist or ("add_to_waitlist" in request.GET)) and request.user.is_eighth_admin

        exception = eighth_exceptions.SignupException()

        if user.grade and user.grade.number > 12:
            exception.SignupForbidden = True

        all_sched_act = [self]
        all_blocks = [self.block]

        # Finds the other scheduling of the same activity on the same day
        # See note above in get_both_blocks_sibling()
        sibling = self.get_both_blocks_sibling()
        if sibling:
            all_sched_act.append(sibling)
            all_blocks.append(sibling.block)

        # Lock on the User and the EighthScheduledActivity to prevent duplicates.
        logger.debug("Locking on user %d and scheduled activity %d", user.id, self.id)
        lock_on([user, self])
        logger.debug("Successfully locked on user %d and scheduled activity %d", user.id, self.id)

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
            if (
                EighthSignup.objects.filter(user=user, scheduled_activity__block__in=all_blocks)
                .filter(Q(scheduled_activity__activity__sticky=True) | Q(scheduled_activity__sticky=True))
                .filter(Q(scheduled_activity__cancelled=False))
                .exists()
            ):
                exception.Sticky = True

            for sched_act in all_sched_act:
                # Check if the block has been locked
                if sched_act.block.locked:
                    exception.BlockLocked = True

                # Check if the scheduled activity has been cancelled
                if sched_act.cancelled:
                    exception.ScheduledActivityCancelled = True

                # Check if the activity is full
                # pylint: disable=too-many-boolean-expressions
                if settings.ENABLE_WAITLIST and (
                    add_to_waitlist
                    or (
                        sched_act.is_full()
                        and not self.is_both_blocks()
                        and (request is not None and not request.user.is_eighth_admin and request.user.is_student)
                    )
                ):
                    # pylint: enable=too-many-boolean-expressions
                    if user.primary_email_address:
                        if EighthWaitlist.objects.filter(user_id=user.id, block_id=self.block.id).exists():
                            EighthWaitlist.objects.filter(user_id=user.id, block_id=self.block.id).delete()
                        waitlist = EighthWaitlist.objects.create(user=user, block=self.block, scheduled_activity=sched_act)
                    else:
                        exception.PrimaryEmailNotSet = True
                elif sched_act.is_full(nocache=True):
                    exception.ActivityFull = True

            # Check if it's too early to sign up for the activity
            if self.activity.presign:
                if self.is_too_early_to_signup():
                    exception.Presign = True

            # Check if signup would violate one-a-day constraint
            if not self.is_both_blocks() and self.activity.one_a_day:
                in_act = (
                    EighthSignup.objects.exclude(scheduled_activity__block=self.block)
                    .filter(user=user, scheduled_activity__block__date=self.block.date, scheduled_activity__activity=self.activity)
                    .exists()
                )
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
                    existing_signup = EighthSignup.objects.nocache().get(user=user, scheduled_activity__block=self.block)
                except EighthSignup.DoesNotExist:
                    add_breadcrumb(
                        category="eighth-signup",
                        message="Signing user {} up for single-block activity {} in block {}".format(user.id, self.activity.id, self.block.id),
                        level="debug",
                    )

                    logger.debug("Signing user %d up for single-block activity %d in block %d", user.id, self.activity.id, self.block.id)

                    signup = EighthSignup.objects.create_signup(
                        user=user, scheduled_activity=self, after_deadline=after_deadline, own_signup=(request is not None and user == request.user)
                    )

                    logger.debug(
                        "Result of new signup existence query: %s",
                        EighthSignup.objects.filter(user=user, scheduled_activity__block=self.block, pk=signup.pk).exists(),
                    )
                    logger.debug(
                        "Result of conflict existence query: %s",
                        EighthSignup.objects.filter(user=user, scheduled_activity__block=self.block).exclude(pk=signup.pk).exists(),
                    )

                    logger.debug("Successfully signed user %d up for single-block activity %d in block %d", user.id, self.activity.id, self.block.id)

                    if signup.has_conflict(nocache=True):
                        try:
                            signup.save()
                        except ValidationError as e:
                            logger.error(
                                "Newly created signup %d (user %d, single-block activity %d, block %d, scheduled activity %d) failed the "
                                "post-creation duplicate check in add_user()",
                                signup.id,
                                user.id,
                                self.activity.id,
                                self.block.id,
                                self.id,
                            )
                            capture_exception(e)
                else:
                    previous_activity_name = existing_signup.scheduled_activity.activity.name_with_flags
                    prev_sponsors = existing_signup.scheduled_activity.get_true_sponsors()
                    previous_activity_sponsors = ", ".join(map(str, prev_sponsors))
                    previous_activity = existing_signup.scheduled_activity

                    if not existing_signup.scheduled_activity.is_both_blocks():
                        add_breadcrumb(
                            category="eighth-signup",
                            message="Switching user {} from single-block activity {} to single-block activity {} in block {}".format(
                                user.id, existing_signup.scheduled_activity.activity.id, self.activity.id, self.block.id
                            ),
                            level="debug",
                        )

                        logger.debug(
                            "Switching user %d from single-block activity %d to single-block activity %d in block %d",
                            user.id,
                            existing_signup.scheduled_activity.activity.id,
                            self.activity.id,
                            self.block.id,
                        )

                        existing_signup.scheduled_activity = self
                        existing_signup.after_deadline = after_deadline
                        existing_signup.was_absent = False
                        existing_signup.absence_acknowledged = False
                        existing_signup.pass_accepted = False
                        existing_signup.previous_activity_name = previous_activity_name
                        existing_signup.previous_activity_sponsors = previous_activity_sponsors
                        existing_signup.own_signup = request is not None and user == request.user

                        existing_signup.save()
                        invalidate_obj(existing_signup)

                        logger.debug(
                            "Successfully switched user %d from single-block activity %d to single-block activity %d in block %d",
                            user.id,
                            existing_signup.scheduled_activity.activity.id,
                            self.activity.id,
                            self.block.id,
                        )

                        if existing_signup.has_conflict():
                            try:
                                existing_signup.save()
                            except ValidationError as e:
                                logger.error(
                                    "Reused signup %d (user %d, single-block activity %d, block %d, scheduled activity %d) failed the post-creation "
                                    "duplicate check in add_user()",
                                    existing_signup.id,
                                    user.id,
                                    self.activity.id,
                                    self.block.id,
                                    self.id,
                                )
                                capture_exception(e)
                    else:
                        # Clear out the other signups for this block if the user is
                        # switching out of a both-blocks activity
                        sibling = existing_signup.scheduled_activity.get_both_blocks_sibling()
                        existing_blocks = [existing_signup.scheduled_activity.block]
                        if sibling:
                            existing_blocks.append(sibling.block)

                        add_breadcrumb(
                            category="eighth-signup",
                            message="Switching user {} from dual-block activity {} to single-block activity {} in block {}".format(
                                user.id, existing_signup.scheduled_activity.activity.id, self.activity.id, self.block.id
                            ),
                            level="debug",
                        )

                        logger.debug(
                            "Switching user %d from dual-block activity %d to single-block activity %d in block %d",
                            user.id,
                            existing_signup.scheduled_activity.activity.id,
                            self.activity.id,
                            self.block.id,
                        )

                        EighthSignup.objects.filter(user=user, scheduled_activity__block__in=existing_blocks).delete()
                        EighthWaitlist.objects.filter(user=user, scheduled_activity=self).delete()
                        signup = EighthSignup.objects.create_signup(
                            user=user,
                            scheduled_activity=self,
                            after_deadline=after_deadline,
                            previous_activity_name=previous_activity_name,
                            previous_activity_sponsors=previous_activity_sponsors,
                            own_signup=(request is not None and user == request.user),
                        )

                        logger.debug(
                            "Successfully switched user %d from dual-block activity %d to single-block activity %d in block %d",
                            user.id,
                            existing_signup.scheduled_activity.activity.id,
                            self.activity.id,
                            self.block.id,
                        )

                        if signup.has_conflict():
                            try:
                                signup.save()
                            except ValidationError as e:
                                logger.error(
                                    "Newly created signup %d created to switch out of dual-block activity (user %d, single-block activity %d, block "
                                    "%d, scheduled activity %d) failed the post-creation duplicate check in add_user()",
                                    existing_signup.id,
                                    user.id,
                                    self.activity.id,
                                    self.block.id,
                                    self.id,
                                )
                                capture_exception(e)

                    if settings.ENABLE_WAITLIST and (
                        previous_activity.waitlist.all().exists()
                        and not self.block.locked
                        and request is not None
                        and not request.session.get("disable_waitlist_transactions", False)
                    ):
                        if not previous_activity.is_full():
                            waitlists = EighthWaitlist.objects.get_next_waitlist(previous_activity)
                            self.notify_waitlist(waitlists)
            else:
                existing_signups = EighthSignup.objects.filter(user=user, scheduled_activity__block__in=all_blocks)

                first_signup = existing_signups.first()
                prev_sched_act = first_signup.scheduled_activity if first_signup is not None else None
                if prev_sched_act is None:
                    logger.debug(
                        "Signing user %d up for double-block activity %d during block %d and its sibling", user.id, self.activity.id, self.block.id
                    )
                else:
                    logger.debug(
                        "Switching user %d from activity %d to double-block activity %d during block %d (and also its sibling)",
                        user.id,
                        prev_sched_act.activity.id,
                        self.activity.id,
                        self.block.id,
                    )

                prev_data = {}
                for signup in existing_signups:
                    add_breadcrumb(
                        category="eighth-signup",
                        message="User {}: original activity for block {}: {}".format(
                            user.id, signup.scheduled_activity.block.id, signup.scheduled_activity.activity.id
                        ),
                        level="debug",
                    )

                    prev_sponsors = signup.scheduled_activity.get_true_sponsors()
                    prev_data[signup.scheduled_activity.block.block_letter] = {
                        "name": signup.scheduled_activity.activity.name_with_flags,
                        "sponsors": ", ".join(map(str, prev_sponsors)),
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

                    add_breadcrumb(
                        category="eighth-signup",
                        message="Switching user {} to double-block activity {} in block {}".format(user.id, sched_act.id, self.block.id),
                        level="debug",
                    )

                    signup = EighthSignup.objects.create_signup(
                        user=user,
                        scheduled_activity=sched_act,
                        after_deadline=after_deadline,
                        previous_activity_name=previous_activity_name,
                        previous_activity_sponsors=previous_activity_sponsors,
                        own_signup=(request is not None and user == request.user),
                    )

                    if signup.has_conflict():
                        try:
                            signup.save()
                        except ValidationError as e:
                            logger.error(
                                "Newly created signup %d created to sign up for dual-block activity (user %d, activity %d, block %d, scheduled "
                                "activity %d) failed the post-creation duplicate check in add_user()",
                                signup.id,
                                user.id,
                                sched_act.activity.id,
                                sched_act.block.id,
                                sched_act.id,
                            )
                            capture_exception(e)

                    # signup.previous_activity_name = signup.activity.name_with_flags
                    # signup.previous_activity_sponsors = ", ".join(map(str, signup.get_true_sponsors()))

                if prev_sched_act is None:
                    logger.debug(
                        "Successfully signed user %d up for double-block activity %d during block %d and its sibling",
                        user.id,
                        self.activity.id,
                        self.block.id,
                    )
                else:
                    logger.debug(
                        "Successfully switched user %d from activity %d to double-block activity %d during block %d (and also its sibling)",
                        user.id,
                        prev_sched_act.activity.id,
                        self.activity.id,
                        self.block.id,
                    )

        return success_message

    def cancel(self):
        """Cancel an EighthScheduledActivity and send a notification email to signed-up students.
        This method should be always be called instead of setting the 'cancelled' flag manually.
        (Note: To avoid spamming students signed up for both-block activities, an email is not sent
        for the B-block activity in both-block activities.)

        """

        if not self.cancelled:
            self.cancelled = True
            self.save(update_fields=["cancelled"])

            if not self.is_both_blocks or self.block.block_letter != "B":
                from .notifications import activity_cancelled_email  # pylint: disable=import-outside-toplevel,cyclic-import

                activity_cancelled_email(self)

    def uncancel(self):
        """Uncancel an EighthScheduledActivity.

        This does nothing besides unset the cancelled flag and save the
        object.

        """

        if self.cancelled:
            self.cancelled = False
            self.save(update_fields=["cancelled"])

    def save(self, *args, **kwargs):  # pylint: disable=signature-differs
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

    def create_signup(self, user: "get_user_model()", scheduled_activity: "EighthScheduledActivity", **kwargs) -> "EighthSignup":
        """Creates an EighthSignup for the given user in the given activity after checking for duplicate signups.

        This raises an error if there are duplicate signups.

        Args:
            user: The user to create the EighthSignup for.
            scheduled_activity: The EighthScheduledActivity to sign the user up for.

        """
        if EighthSignup.objects.filter(user=user, scheduled_activity__block=scheduled_activity.block).nocache().exists():
            logger.error(
                "Duplicate signup before creating signup for user %d in activity %d, block %d, scheduled activity %d",
                user.id,
                scheduled_activity.activity.id,
                scheduled_activity.block.id,
                scheduled_activity.id,
            )
            raise ValidationError("EighthSignup already exists for this user on this block.")

        signup = self.create(user=user, scheduled_activity=scheduled_activity, **kwargs)

        if EighthSignup.objects.exclude(pk=signup.pk).filter(user=user, scheduled_activity__block=scheduled_activity.block).nocache().exists():
            logger.error(
                "Duplicate signup after creating signup %d to sign up user %d in activity %d, block %d, scheduled activity %d; deleting",
                signup.id,
                user.id,
                scheduled_activity.activity.id,
                scheduled_activity.block.id,
                scheduled_activity.id,
            )
            signup.delete()
            raise ValidationError("EighthSignup already exists for this user on this block.")

        return signup

    def get_absences(self) -> Union[QuerySet, Collection["EighthSignup"]]:  # pylint: disable=unsubscriptable-object
        """Returns all EighthSignups for which the student was marked as absent.

        Returns:
            A QuerySet of all the EighthSignups for which the student was marked as absent.

        """
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
    scheduled_activity = models.ForeignKey(
        EighthScheduledActivity, related_name="eighthsignup_set", null=False, db_index=True, on_delete=models.CASCADE
    )

    # An after-deadline signup is assumed to be a pass
    after_deadline = models.BooleanField(default=False)
    previous_activity_name = models.CharField(max_length=200, blank=True, null=True, default=None)
    previous_activity_sponsors = models.CharField(max_length=10000, blank=True, null=True, default=None)

    pass_accepted = models.BooleanField(default=False, blank=True)
    was_absent = models.BooleanField(default=False, blank=True)
    absence_acknowledged = models.BooleanField(default=False, blank=True)
    absence_emailed = models.BooleanField(default=False, blank=True)

    archived_was_absent = models.BooleanField(default=False, blank=True)

    def save(self, *args, **kwargs):  # pylint: disable=signature-differs
        if self.has_conflict(nocache=True):
            logger.error(
                "Duplicate signup while saving signup %d for user %d in activity %d, block %d, scheduled activity %d",
                self.id,
                self.user.id,
                self.scheduled_activity.activity.id,
                self.scheduled_activity.block.id,
                self.scheduled_activity.id,
            )
            raise ValidationError("EighthSignup already exists for this user on this block.")
        super(EighthSignup, self).save(*args, **kwargs)

    own_signup = models.BooleanField(default=False)

    history = HistoricalRecords()

    def validate_unique(self, *args, **kwargs):  # pylint: disable=signature-differs
        """Checked whether more than one EighthSignup exists for a User on a given EighthBlock."""
        super(EighthSignup, self).validate_unique(*args, **kwargs)

        if self.has_conflict(nocache=True):
            raise ValidationError({NON_FIELD_ERRORS: ("EighthSignup already exists for the User and the EighthScheduledActivity's block",)})

    def has_conflict(self, nocache: bool = False) -> bool:
        """Returns True if another EighthSignup object exists for the same user in the same block.

        Args:
            nocache: Whether to explicitly disable caching for this check.

        Returns:
            Whether there is another EighthSignup for the same user in the same block.

        """
        q = EighthSignup.objects.exclude(pk=self.pk).filter(user=self.user, scheduled_activity__block=self.scheduled_activity.block)
        if nocache:
            q = q.nocache()

        return q.exists()

    def remove_signup(self, user: "get_user_model()" = None, force: bool = False, dont_run_waitlist: bool = False) -> str:
        """Attempts to remove the EighthSignup if the user has permission to do so.

        Args:
            user: The user who is attempting to remove the EighthSignup.
            force: Whether to force removal.
            dont_run_waitlist: Whether to skip notifying users on the activity's waitlist.

        Returns:
            A message to be displayed to the user indicating successful removal.

        """

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
        if self.scheduled_activity.activity and self.scheduled_activity.activity.sticky and not self.scheduled_activity.cancelled:
            exception.Sticky = True

        if exception.messages() and not force:
            raise exception
        else:
            block = self.scheduled_activity.block
            self.delete()
            if settings.ENABLE_WAITLIST and self.scheduled_activity.waitlist.all().exists() and not block.locked and not dont_run_waitlist:
                if not self.scheduled_activity.is_full():
                    waitlists = EighthWaitlist.objects.get_next_waitlist(self.scheduled_activity)
                    self.scheduled_activity.notify_waitlist(waitlists)
            return "Successfully removed signup for {}.".format(block)

    def accept_pass(self):
        """Accepts an eighth period pass for the EighthSignup object."""
        self.was_absent = False
        self.pass_accepted = True
        self.save(update_fields=["was_absent", "pass_accepted"])

    def reject_pass(self):
        """Rejects an eighth period pass for the EighthSignup object."""
        self.was_absent = True
        self.pass_accepted = True
        self.save(update_fields=["was_absent", "pass_accepted"])

    def in_clear_absence_period(self) -> bool:
        """Returns whether the block for this signup is in the clear absence period.

        Returns:
            Whether the block for this signup is in the clear absence period.

        """
        return self.scheduled_activity.block.in_clear_absence_period()

    def archive_remove_absence(self):
        """If user was absent, archives the absence."""
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

    def get_next_waitlist(
        self, activity: EighthScheduledActivity
    ) -> Union[QuerySet, Collection["EighthWaitlist"]]:  # pylint: disable=unsubscriptable-object
        """Returns a QuerySet of all the EighthWaitlist objects for the given
        activity, ordered by signup time.

        Args:
            activity: The activity to list the EighthWaitlist objects for.

        Returns:
            A QuerySet of all the EighthWaitlist objects for the given activity,
            ordered by signup time.

        """
        return self.filter(scheduled_activity_id=activity.id).order_by("time")

    def check_for_prescence(self, activity: EighthScheduledActivity, user: "get_user_model()") -> bool:
        """Returns whether the given user is in a waitlist for the given activity.

        Args:
            activity: The activity for which the waitlist should be queried.
            user: The user who should be searched for in the activity's waitlist.

        Returns:
            Whether the given user is in a waitlist for the given activity.

        """
        return self.filter(scheduled_activity_id=activity.id, user=user).exists()

    def position_in_waitlist(self, aid: int, uid: int) -> int:
        """Given an activity ID and a user ID, returns the user's position in the waitlist (starting at 1).
        If the user is not in the waitlist, returns 0.

        Args:
            aid: The ID of the EighthScheduledActivity for which the waitlist should be queried.
            uid: The ID of the user whose position in the waitlist should be found.

        Returns:
            The user's position in the waitlist, starting at 1, or 0 if the user is not in the waitlist.

        """
        try:
            return self.filter(scheduled_activity_id=aid, time__lt=self.get(scheduled_activity_id=aid, user_id=uid).time).count() + 1
        except EighthWaitlist.DoesNotExist:
            return 0


class EighthWaitlist(AbstractBaseEighthModel):
    objects = EighthWaitlistManager()
    time = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=False, on_delete=set_historical_user)
    block = models.ForeignKey(EighthBlock, null=False, on_delete=models.CASCADE)
    scheduled_activity = models.ForeignKey(
        EighthScheduledActivity, related_name="eighthwaitlist_set", null=False, db_index=True, on_delete=models.CASCADE
    )

    def __str__(self):
        return "{}: {}".format(self.user, self.scheduled_activity)


class EighthActivitySimilarity(AbstractBaseEighthModel):
    count = models.IntegerField()
    weighted = models.FloatField()

    @property
    def _weighted(self) -> float:
        cap = self.activity_set.first().capacity() + self.activity_set.last().capacity()
        if cap == 0:
            cap = 100
        return self.count / cap

    def update_weighted(self):
        """Recalculates the 'weighted' field based on changes to similar activities."""
        self.weighted = self._weighted
        self.save(update_fields=["weighted"])

    def __str__(self):
        act_set = self.activity_set.all()
        return "{} and {}: {}".format(act_set.first(), act_set.last(), self.count)
