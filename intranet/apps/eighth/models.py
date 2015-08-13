
from __future__ import unicode_literals

from itertools import chain
import logging
import datetime
from django.db import models
from django.db.models import Manager, Q
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.utils import formats
from ..users.models import User
from . import exceptions as eighth_exceptions

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
            A :class:`User<intranet.apps.users.models.User>` object
            linked to the sponsor.
        online_attendance
            Whether the sponsor takes attendance online.
        show_full_name
            Whether to always show the sponsor's full name
            (e.x. because there are two teachers named Lewis)
    """

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    user = models.OneToOneField(User, null=True, blank=True)
    online_attendance = models.BooleanField(default=True)
    show_full_name = models.BooleanField(default=False)

    class Meta:
        unique_together = (("first_name",
                            "last_name",
                            "user",
                            "online_attendance"),)
        ordering = ("last_name", "first_name",)

    @property
    def name(self):
        if self.show_full_name and self.first_name:
            return self.last_name + ", " + self.first_name
        else:
            return self.last_name

    def __unicode__(self):
        return self.name


class EighthRoom(AbstractBaseEighthModel):

    """Represents a room in which an eighth period activity can be held

    Attributes:
        name
            The name of the room.
        capacity
            The maximum capacity of the room (-1 for unlimited, 0 to prevent student signup)

    """
    name = models.CharField(max_length=100)
    capacity = models.SmallIntegerField(default=28)

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

    def __unicode__(self):
        return "{} ({})".format(self.name, self.capacity)

    class Meta:
        ordering = ("name",)


class EighthActivityExcludeDeletedManager(models.Manager):

    def get_query_set(self):
        return (super(EighthActivityExcludeDeletedManager, self).get_query_set()
                                                                .exclude(deleted=True))


class EighthActivity(AbstractBaseEighthModel):

    """Represents an eighth period activity.

    Attributes:
        aid
            The AID (activity ID), not the same as the activity's ID necessarily. By default,
            it is the same as the assigned ID. However, it can be changed to any alphanumeric
            string that is between 1-10 characters. Don't set to the internal ID of another
            activity, or to the AID of another activity.
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
        users_allowed
            Individual users allowed to sign up for this activity. Extensive use of this is discouraged; make
            a group instead through the "Add and Assign Empty Group" button on the Edit Activity page. Only
            takes effect if the activity is restricted.
        groups_allowed
            Individual groups allowed to sign up for this activity. Only takes effect if the activity is
            restricted.
        freshman_allowed, sophomores_allowed, juniors_allowed, seniors_allowed
            Whether Freshman/Sophomores/Juniors/Seniors are allowed to sign up for this activity. Only
            takes effect if the activity is restricted.
        favorites
            A ManyToManyField of User objects who have favorited the activity.
        deleted
            Whether the activity still technically exists in the system, but was marked to be deleted.

    """
    objects = models.Manager()
    undeleted_objects = EighthActivityExcludeDeletedManager()

    aid = models.CharField(max_length=10, blank=True) # Should be unique
    name = models.CharField(max_length=100)  # This should really be unique
    description = models.CharField(max_length=2000, blank=True)
    sponsors = models.ManyToManyField(EighthSponsor, blank=True)
    rooms = models.ManyToManyField(EighthRoom, blank=True)

    presign = models.BooleanField(default=False)
    one_a_day = models.BooleanField(default=False)
    both_blocks = models.BooleanField(default=False)
    sticky = models.BooleanField(default=False)
    special = models.BooleanField(default=False)
    administrative = models.BooleanField(default=False)

    restricted = models.BooleanField(default=False)

    users_allowed = models.ManyToManyField(User,
                                           related_name="restricted_activity_set",
                                           blank=True)
    groups_allowed = models.ManyToManyField(Group,
                                            related_name="restricted_activity_set",
                                            blank=True)

    freshmen_allowed = models.BooleanField(default=False)
    sophomores_allowed = models.BooleanField(default=False)
    juniors_allowed = models.BooleanField(default=False)
    seniors_allowed = models.BooleanField(default=False)

    favorites = models.ManyToManyField(User,
                                       related_name="favorited_activity_set",
                                       blank=True)

    deleted = models.BooleanField(blank=True, default=False)

    def capacity(self):
        # Note that this is the default capacity if the
        # rooms/capacity are not overridden for a particular block.

        rooms = self.rooms.all()
        return EighthRoom.total_capacity_of_rooms(rooms)

    @property
    def name_with_flags(self):
        """Return the activity name with special, both blocks,
        restricted, administrative, sticky, and deleted flags."""
        return self._name_with_flags(True)

    @property
    def name_with_flags_no_restricted(self):
        """Return the activity name with special, both blocks,
        administrative, sticky, and deleted flags."""
        return self._name_with_flags(False)

    def _name_with_flags(self, include_restricted, title=None):
        """Generate the name with flags."""
        name = "Special: " if self.special else ""
        name += self.name
        if title:
            name += " - {}".format(title)
        if include_restricted:
            name += " (R)" if self.restricted else ""
        name += " (BB)" if self.both_blocks else ""
        name += " (A)" if self.administrative else ""
        name += " (S)" if self.sticky else ""
        name += " (Deleted)" if self.deleted else ""
        return name

    @classmethod
    def restricted_activities_available_to_user(cls, user):
        """Find the restricted activities available to the given user."""
        activities = set(user.restricted_activity_set
                             .values_list("id", flat=True))

        grade = user.grade.number

        if grade == 9:
            activities |= set(EighthActivity.objects
                                            .filter(freshmen_allowed=True)
                                            .values_list("id", flat=True))
        elif grade == 10:
            activities |= set(EighthActivity.objects
                                            .filter(sophomores_allowed=True)
                                            .values_list("id", flat=True))
        elif grade == 11:
            activities |= set(EighthActivity.objects
                                            .filter(juniors_allowed=True)
                                            .values_list("id", flat=True))
        elif grade == 12:
            activities |= set(EighthActivity.objects
                                            .filter(seniors_allowed=True)
                                            .values_list("id", flat=True))

        for group in user.groups.all():
            activities |= set(group.restricted_activity_set
                                   .values_list("id", flat=True))

        return list(activities)

    def save(self, *args, **kwargs):
        """When saving the model, update the AID to
        be the internal ID if it is blank or None.
        """
        update_aid = False


        if not self.aid:
            if self.pk:
                self.aid = self.pk
            else:
                update_aid = True
        else:
            with_aid = EighthActivity.objects.filter(aid=self.aid)
            if len(with_aid) == 0 or (len(with_aid) == 1 and with_aid[0] == self):
                update_aid = False
            else:
                # aid is not unique
                raise ValidationError("AID is not unique.")

        super(EighthActivity, self).save(*args, **kwargs)

        if update_aid:
            # Update aid with new ID and re-save
            self.aid = self.pk
            super(EighthActivity, self).save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "eighth activities"

    def __unicode__(self):
        return self.name_with_flags


class EighthBlockManager(models.Manager):

    def get_first_upcoming_block(self):
        """Gets the first upcoming block (the first block that will
        take place in the future). If there is no block in the future,
        the most recent block will be returned

        Returns: the `EighthBlock` object

        """

        now = datetime.datetime.now()

        # Show same day if it's before 17:00
        if now.hour < 17:
            now = now.replace(hour=0, minute=0, second=0, microsecond=0)

        block = self.order_by("date", "block_letter").filter(date__gte=now).first()
        return block

    def get_next_upcoming_blocks(self):
        """Gets the next upccoming blocks. (Finds the other blocks
           that are occurring on the day of the first upcoming block.)
            
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
            block = (self.prefetch_related("eighthscheduledactivity_set")
                         .get(id=first_upcoming_block.id))
        except EighthBlock.DoesNotExist:
            return []

        return block.get_surrounding_blocks()


class EighthBlock(AbstractBaseEighthModel):

    """Represents an eighth period block.

    Attributes:
        date
            The date of the block.
        signup_time
            The recommended time at which all users should sign up.
            This does *not* prevent people from signing up at this
            time, however students will see the amount of time left
            to sign up. Defaults to 12:30.
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
    signup_time = models.TimeField(default=datetime.time(12,30))
    block_letter = models.CharField(max_length=10)
    locked = models.BooleanField(default=False)
    activities = models.ManyToManyField(EighthActivity,
                                        through="EighthScheduledActivity",
                                        blank=True)
    comments = models.CharField(max_length=100, blank=True)

    override_blocks = models.ManyToManyField("EighthBlock", blank=True)

    def save(self, *args, **kwargs):
        """Capitalize the first letter of the block name."""
        letter = getattr(self, "block_letter", None)
        if letter and len(letter) >= 1:
            self.block_letter = letter[:1].upper() + letter[1:]

        super(EighthBlock, self).save(*args, **kwargs)

    def next_blocks(self, quantity=-1):
        """Get the next blocks in order."""
        blocks = (EighthBlock.objects
                             .order_by("date", "block_letter")
                             .filter(Q(date__gt=self.date)
                                     | (Q(date=self.date)
                                        & Q(block_letter__gt=self.block_letter))
                                     ))
        if quantity == -1:
            return blocks
        return blocks[:quantity + 1]

    def previous_blocks(self, quantity=-1):
        """Get the previous blocks in order."""
        blocks = (EighthBlock.objects
                             .order_by("-date", "-block_letter")
                             .filter(Q(date__lt=self.date)
                                     | (Q(date=self.date)
                                        & Q(block_letter__lt=self.block_letter))
                                     ))
        if quantity == -1:
            return reversed(blocks)
        return reversed(blocks[:quantity + 1])

    def get_surrounding_blocks(self):
        """Get the blocks around the one given.
           Returns: a list of all of those blocks."""

        next = self.next_blocks()
        prev = self.previous_blocks()

        surrounding_blocks = list(chain(prev, [self], next))
        return surrounding_blocks

    def is_today(self):
        """Does the block occur today?"""
        return datetime.date.today() == self.date

    def signup_time_future(self):
        """Is the signup time in the future?"""
        return self.signup_time > datetime.datetime.now().time()

    def num_signups(self):
        """ How many people have signed up?"""
        return EighthSignup.objects.filter(scheduled_activity__block=self).count()

    @property
    def letter_width(self):
        return (len(self.block_letter) - 1) * 6 + 15

    @property
    def letter_text(self):
        if any(char.isdigit() for char in self.block_letter):
            return "Block {}".format(self.block_letter)
        else:
            return "{} Block".format(self.block_letter)

    def __unicode__(self):
        formatted_date = formats.date_format(self.date, "EIGHTH_BLOCK_DATE_FORMAT")
        return "{} ({})".format(formatted_date, self.block_letter)

    class Meta:
        unique_together = (("date", "block_letter"),)
        ordering = ("date", "block_letter")


class EighthScheduledActivityManager(Manager):
    """Model Manager for EighthScheduledActivity"""

    def for_sponsor(cls, sponsor):
        """Return a QueryList of EighthScheduledActivities where the given
        EighthSponsor is sponsoring.

        If a sponsorship is defined in an EighthActivity, it may be overridden
        on a block by block basis in an EighthScheduledActivity. Sponsors from
        the EighthActivity do not carry over.

        EighthScheduledActivities that are deleted or cancelled are also not
        counted.

        """
        sponsoring_filter = (Q(sponsors=sponsor) |
                             (Q(sponsors=None) & Q(activity__sponsors=sponsor)))
        sched_acts = (EighthScheduledActivity.objects
                                             .exclude(activity__deleted=True)
                                             .exclude(cancelled=True)
                                             .filter(sponsoring_filter))
        return sched_acts


class EighthScheduledActivity(AbstractBaseEighthModel):

    """Represents the relationship between an activity and a block in
    which it has been scheduled.

    Attributes:
        block : :class:`EighthBlock`
            The :class:`EighthBlock` during which an
            :class:`EighthActivity` has been scheduled
        activity
            The scheduled :class:`EighthActivity`
        members
            The :class:`User<intranet.apps.users.models.User>`\s who have
            signed up for an :class:`EighthBlock`
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
            whether the :class:`EighthSponsor` for the scheduled
            :class:`EighthActivity` has taken attendance yet
        cancelled
            whether the :class:`EighthScheduledActivity` has been cancelled

    """

    # Use model manager
    objects = EighthScheduledActivityManager()

    block = models.ForeignKey(EighthBlock)
    activity = models.ForeignKey(EighthActivity)
    members = models.ManyToManyField(
        User,
        through="EighthSignup",
        related_name="eighthscheduledactivity_set"
    )

    admin_comments = models.CharField(max_length=1000, blank=True)
    title = models.CharField(max_length=1000, blank=True)
    comments = models.CharField(max_length=1000, blank=True)

    # Overridden attributes
    sponsors = models.ManyToManyField(EighthSponsor, blank=True)
    rooms = models.ManyToManyField(EighthRoom, blank=True)
    capacity = models.SmallIntegerField(null=True, blank=True)

    attendance_taken = models.BooleanField(default=False)
    cancelled = models.BooleanField(default=False)

    @property
    def full_title(self):
        """Gets the full title for the activity, appending the title of the
        scheduled activity to the activity's name.
        """
        cancelled_str = " (Cancelled)" if self.cancelled else ""
        act_name = self.activity.name + cancelled_str
        return act_name if not self.title else "{} - {}".format(act_name, self.title)

    @property
    def title_with_flags(self):
        """Gets the title for the activity, appending the title of the
        scheduled activity to the activity's name and flags.
        """
        cancelled_str = " (Cancelled)" if self.cancelled else ""
        name_with_flags = self.activity._name_with_flags(True, self.title) + cancelled_str
        return name_with_flags

    def get_true_sponsors(self):
        """Get the sponsors for the scheduled activity, taking into account
        activity defaults and overrides.
        """

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
        """Get the rooms for the scheduled activity, taking into account
        activity defaults and overrides.

        """

        rooms = self.rooms.all()
        if len(rooms) > 0:
            return rooms
        else:
            return self.activity.rooms.all()

    def get_true_capacity(self):
        """Get the capacity for the scheduled activity, taking into
        account activity defaults and overrides.

        """

        c = self.capacity
        if c is not None:
            return c
        else:
            rooms = self.get_true_rooms()
            return EighthRoom.total_capacity_of_rooms(rooms)

    def is_full(self):
        """Return whether the activity is full.

        """
        capacity = self.get_true_capacity()
        if capacity != -1:
            num_signed_up = self.eighthsignup_set.count()
            return num_signed_up >= capacity
        return False

    def is_overbooked(self):
        """Return whether the activity is overbooked.

        """
        capacity = self.get_true_capacity()
        if capacity != -1:
            num_signed_up = self.eighthsignup_set.count()
            return num_signed_up > capacity
        return False

    def is_too_early_to_signup(self, now=None):
        """Return whether it is too early to sign up for the
        activity if it is a presign (48 hour logic is here).

        """
        if now is None:
            now = datetime.datetime.now()

        activity_date = (datetime.datetime
                                 .combine(self.block.date,
                                          datetime.time(0, 0, 0)))
        # Presign activities can only be signed up for 2 days in advance.
        presign_period = datetime.timedelta(days=2)

        return (now < (activity_date - presign_period))

    def has_open_passes(self):
        """Return whether there are passes that have not been acknowledged.

        """
        return self.eighthsignup_set.filter(after_deadline=True, pass_accepted=False)

    def get_viewable_members(self, user=None):
        """Get the list of members that you have permissions to view.

        Returns: List of members
        """
        members = []
        for member in self.members.all():
            show = False
            show = member.can_view_eighth
            if user and user.is_eighth_admin:
                show = True
            if member == user:
                show = True
            if show:
                members.append(member)

        return members

    def get_hidden_members(self, user=None):
        """Get the number of members that you do not have permission to view.

        Returns: Number of members hidden based on preferences
        """
        hidden_members = []
        for member in self.members.all():
            show = False
            show = member.can_view_eighth
            if user and user.is_eighth_admin:
                show = True
            if member == user:
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
        if not self.activity.both_blocks:
            return None

        if not self.block.block_letter in ["A", "B"]:
            # both_blocks is not currently implemented for blocks other than A and B
            return None

        other_instances = (EighthScheduledActivity.objects.filter(activity=self.activity,
                                                                  block__date=self.block.date))

        for inst in other_instances:
            if inst == self:
                continue

            if inst.block_letter in ["A", "B"]:
                return inst

        return False

    def add_user(self, user, request=None, force=False):
        """Sign up a user to this scheduled activity if possible.
        This is where the magic happens.

        Raises an exception if there's a problem signing the user up
        unless the signup is forced.

        """
        if request is not None:
            force = (force or ("force" in request.GET)) and request.user.is_eighth_admin

        exception = eighth_exceptions.SignupException()

        if not force:
            # Check if the user who sent the request has the permissions
            # to change the target user's signups
            if request is not None:
                if user != request.user and not request.user.is_eighth_admin:
                    exception.SignupForbidden = True
                    raise exception

            if self.activity.both_blocks:
                # Finds the other scheduling of the same activity on the same day
                # See note above in get_both_blocks_sibling()
                sibling = self.get_both_blocks_sibling()
                if sibling:
                    all_sched_act = [self, sibling]
                else:
                    all_sched_act = [self]
            else:
                all_sched_act = [self]

            # Check if the block has been locked
            for sched_act in all_sched_act:
                if sched_act.block.locked:
                    exception.BlockLocked = True

            # Check if the scheduled activity has been cancelled
            for sched_act in all_sched_act:
                if sched_act.cancelled:
                    exception.ScheduledActivityCancelled = True

            # Check if the activity has been deleted
            if self.activity.deleted:
                exception.ActivityDeleted = True

            # Check if the activity is full
            for sched_act in all_sched_act:
                if sched_act.is_full():
                    exception.ActivityFull = True

            # Check if it's too early to sign up for the activity
            if self.activity.presign:
                if self.is_too_early_to_signup():
                    exception.Presign = True

            # Check if the user is already stickied into an activity
            if not self.activity.both_blocks:
                in_stickie = (EighthSignup.objects
                                          .filter(user=user,
                                                  scheduled_activity__activity__sticky=True,
                                                  scheduled_activity__block=self.block)
                                          .exists())
            else:
                in_stickie = (EighthSignup.objects
                                          .filter(user=user,
                                                  scheduled_activity__activity__sticky=True,
                                                  scheduled_activity__in=all_sched_act)
                                          .exists())
            if in_stickie:
                exception.Sticky = True

            # Check if signup would violate one-a-day constraint
            if not self.activity.both_blocks and self.activity.one_a_day:
                in_act = (EighthSignup.objects
                                      .exclude(scheduled_activity__block=self.block)
                                      .filter(user=user,
                                              scheduled_activity__block__date=self.block.date,
                                              scheduled_activity__activity=self.activity)
                                      .exists())
                if in_act:
                    exception.OneADay = True

            # Check if user is allowed in the activity if it's restricted
            if self.activity.restricted:
                acts = EighthActivity.restricted_activities_available_to_user(user)
                if self.activity.id not in acts:
                    exception.Restricted = True

        success_message = "Successfully signed up for activity. "

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
                        logger.debug("Need to remove signup for {}".format(signup))
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
        if not self.activity.both_blocks:
            try:
                existing_signup = (EighthSignup.objects
                                               .get(user=user,
                                                    scheduled_activity__block=self.block))

                previous_activity_name = existing_signup.scheduled_activity.activity.name_with_flags
                prev_sponsors = existing_signup.scheduled_activity.get_true_sponsors()
                previous_activity_sponsors = ", ".join(map(str, prev_sponsors))

                if not existing_signup.scheduled_activity.activity.both_blocks:
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
                    sibling = self.get_both_blocks_sibling()
                    all_sched_act = [self]
                    if sibling:
                        all_sched_act.append(sibling)

                    EighthSignup.objects.filter(
                        user=user,
                        scheduled_activity__in=all_sched_act
                    ).delete()
                    EighthSignup.objects.create(user=user,
                                                scheduled_activity=self,
                                                after_deadline=after_deadline,
                                                previous_activity_name=previous_activity_name,
                                                previous_activity_sponsors=previous_activity_sponsors)
            except EighthSignup.DoesNotExist:
                EighthSignup.objects.create(user=user,
                                            scheduled_activity=self,
                                            after_deadline=after_deadline)
        else:

            sibling = self.get_both_blocks_sibling()
            all_sched_act = [self]
            if sibling:
                all_sched_act.append(sibling)

            existing_signups = EighthSignup.objects.filter(
                user=user,
                scheduled_activity__in=all_sched_act
            )

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

                EighthSignup.objects.create(user=user,
                                            scheduled_activity=sched_act,
                                            after_deadline=after_deadline,
                                            previous_activity_name=previous_activity_name,
                                            previous_activity_sponsors=previous_activity_sponsors)

                # signup.previous_activity_name = signup.activity.name_with_flags
                # signup.previous_activity_sponsors = ", ".join(map(str, signup.get_true_sponsors()))

        """
        # See "If block overrides signup on other blocks" check
        # If there are EighthSignups that need to be removed, do them at the end
        for signup in final_remove_signups:
            success_message += "\nYour signup for {} on {} was removed. ".format(signup.scheduled_activity.activity, signup.scheduled_activity.block)
            signup.delete()
        """

        return success_message

    def cancel(self):
        """Cancel an EighthScheduledActivity, and update the rooms and sponsors
        to be "CANCELLED."
        """
        #super(EighthScheduledActivity, self).save(*args, **kwargs)

        logger.debug("Running cancel hooks: {}".format(self))

        if not self.cancelled:
            logger.debug("Cancelling {}".format(self))
            self.cancelled = True

        cancelled_room = EighthRoom.objects.get_or_create(name="CANCELLED", capacity=0)[0]
        cancelled_sponsor = EighthSponsor.objects.get_or_create(first_name="", last_name="CANCELLED")[0]
        if cancelled_room not in list(self.rooms.all()):
            self.rooms.all().delete()
            self.rooms.add(cancelled_room)

        if cancelled_sponsor not in list(self.sponsors.all()):
            self.sponsors.all().delete()
            self.sponsors.add(cancelled_sponsor)

        self.save()


    def uncancel(self):
        """Uncancel an EighthScheduledActivity, by removing the "CANCELLED" rooms
        and sponsors.
        """

        logger.debug("Running uncancel hooks: {}".format(self))
        if self.cancelled:
            logger.debug("Uncancelling {}".format(self))
            self.cancelled = False

        cancelled_room = EighthRoom.objects.get_or_create(name="CANCELLED", capacity=0)[0]
        cancelled_sponsor = EighthSponsor.objects.get_or_create(first_name="", last_name="CANCELLED")[0]
        if cancelled_room in list(self.rooms.all()):
            self.rooms.filter(id=cancelled_room.id).delete()

        if cancelled_sponsor in list(self.sponsors.all()):
            self.sponsors.filter(id=cancelled_sponsor.id).delete()

        self.save()

    def save(self, *args, **kwargs):
        super(EighthScheduledActivity, self).save(*args, **kwargs)


    class Meta:
        unique_together = (("block", "activity"),)
        verbose_name_plural = "eighth scheduled activities"

    def __unicode__(self):
        cancelled_str = " (Cancelled)" if self.cancelled else ""
        return "{} on {}{}".format(self.activity, self.block, cancelled_str)


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

    """
    time = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(User, null=False)
    scheduled_activity = models.ForeignKey(
        EighthScheduledActivity,
        related_name="eighthsignup_set",
        null=False,
        db_index=True
    )

    # An after-deadline signup is assumed to be a pass
    after_deadline = models.BooleanField(default=False)
    previous_activity_name = models.CharField(max_length=200, blank=True, null=True, default=None)
    previous_activity_sponsors = models.CharField(max_length=10000, blank=True, null=True, default=None)

    pass_accepted = models.BooleanField(default=False, blank=True)
    was_absent = models.BooleanField(default=False, blank=True)
    absence_acknowledged = models.BooleanField(default=False, blank=True)

    def validate_unique(self, *args, **kwargs):
        """Checked whether more than one EighthSignup exists for a User
        on a given EighthBlock."""
        super(EighthSignup, self).validate_unique(*args, **kwargs)

        not_unique = (self.__class__
                          .objects
                          .exclude(pk=self.pk)
                          .filter(user=self.user,
                                  scheduled_activity__block=self.scheduled_activity.block)
                          .exists())

        if not_unique:
            raise ValidationError({
                NON_FIELD_ERRORS: ("EighthSignup already exists for the User "
                                   "and the EighthScheduledActivity's block",)
            })

    def remove_signup(self, user=None, force=False):
        """Attempt to remove the EighthSignup if the user has permission
        to do so."""

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


    def __unicode__(self):
        return "{}: {}".format(self.user,
                               self.scheduled_activity)

    class Meta:
        unique_together = (("user", "scheduled_activity"),)
