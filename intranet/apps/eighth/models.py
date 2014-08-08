# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from itertools import chain
import logging
import datetime
from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from ..users.models import User

logger = logging.getLogger(__name__)


class EighthSponsor(models.Model):
    """Represents a sponsor for an eighth period activity.

    A sponsor could be an actual user or just a name.

    Attributes:
        - user -- A :class:`User<intranet.apps.users.models.User>`\
                  object for the sponsor.
        - name -- The name of the sponsor

    """
    first_name = models.CharField(null=True, max_length=63)
    last_name = models.CharField(null=True, max_length=63)
    user = models.ForeignKey(User, null=True)
    online_attendance = models.BooleanField(default=True)

    class Meta:
        unique_together = (("first_name", "last_name", "user", "online_attendance"),)

    def __unicode__(self):
        try:
            l = self.last_name
        except NameError:
            l = ""
        try:
            f = self.first_name
        except NameError:
            f = ""
        return "{}, {}".format(l, f)


class EighthRoom(models.Model):
    """Represents a room in which an eighth period activity can be held

    Attributes:
        - Attribute -- Description.

    """
    name = models.CharField(max_length=63)
    capacity = models.SmallIntegerField(default=-1)

    unique_together = (("name", "capacity"),)

    def __unicode__(self):
        return "{} ({})".format(self.name, self.capacity)


class EighthActivity(models.Model):
    """Represents an eighth period activity.

    Attributes:
        - name -- The name of the activity.
        - sponsors -- The :class:`EighthSponsor`s for the activity.

    """

    name = models.CharField(max_length=63, unique=True)
    description = models.TextField(blank=True)
    sponsors = models.ManyToManyField(EighthSponsor, blank=True)
    rooms = models.ManyToManyField(EighthRoom, blank=True)

    restricted = models.BooleanField(default=False)
    presign = models.BooleanField(default=False)
    one_a_day = models.BooleanField(default=False)
    both_blocks = models.BooleanField(default=False)
    sticky = models.BooleanField(default=False)
    special = models.BooleanField(default=False)

    # Groups allowed

    # Single students allowed

    @property
    def capacity(self):
        all_rooms = self.rooms.all()
        if len(all_rooms) == 0:
            capacity = -1
        else:
            capacity = 0
            for room in all_rooms:
                capacity += room.capacity
        return capacity

    class Meta:
        verbose_name_plural = "eighth activities"

    def __unicode__(self):
        return self.name


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

        try:
            block = self.order_by("date", "block_letter") \
                        .filter(date__gte=now)[0]
        except IndexError:
            block = None
        return block

    def get_current_blocks(self):
        try:
            first_upcoming_block = self.get_first_upcoming_block()
            if first_upcoming_block is None:
                raise EighthBlock.DoesNotExist()
            block = self.prefetch_related("eighthscheduledactivity_set") \
                        .get(id=first_upcoming_block.id)
        except EighthBlock.DoesNotExist:
            return []

        return block.get_surrounding_blocks()


class EighthBlock(models.Model):
    """Represents an eighth period block.

    Attributes:
        - date -- The date of the block.
        - block_letter -- The block letter (e.g. A, B).
        - locked -- Whether signups are closed.
        - activities -- List of \
                        :class:`EighthScheduledActivity`s for the block.

    """
    date = models.DateField(null=False)
    block_letter = models.CharField(max_length=1)
    locked = models.BooleanField(default=False)
    activities = models.ManyToManyField(EighthActivity,
                                        through="EighthScheduledActivity",
                                        blank=True)

    objects = EighthBlockManager()

    def save(self, *args, **kwargs):
            letter = getattr(self, "block_letter", None)
            if letter:
                self.block_letter = letter.capitalize()

            super(EighthBlock, self).save(*args, **kwargs)

    def next_blocks(self, quantity=-1):
        blocks = EighthBlock.objects \
                            .order_by("date", "block_letter") \
                            .filter(Q(date__gt=self.date)
                                    | (Q(date=self.date)
                                    & Q(block_letter__gt=self.block_letter)))
        if quantity == -1:
            return blocks
        return blocks[:quantity + 1]

    def previous_blocks(self, quantity=-1):
        blocks = EighthBlock.objects \
                            .order_by("-date", "-block_letter") \
                            .filter(Q(date__lt=self.date)
                                    | (Q(date=self.date)
                                    & Q(block_letter__lt=self.block_letter)))
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

    def __unicode__(self):
        return "{}: {}".format(str(self.date), self.block_letter)

    class Meta:
        unique_together = (("date", "block_letter"),)


class EighthScheduledActivity(models.Model):
    """Represents the relationship between an activity and a block in
    which it has been scheduled.

    Attributes:
        - block -- the :class:`EighthBlock` during which an \
                   :class:`EighthActivity` has been scheduled
        - activity -- the scheduled :class:`EighthActivity`
        - members -- the :class:`User<intranet.apps.users.models.User>`s\
                     who have signed up for an :class:`EighthBlock`
        - comments -- notes for the Eighth Office
        - sponsors -- :class:`EighthSponsor`s that will override the \
                      :class:`EighthActivity`'s default sponsors
        - rooms -- :class:`EighthRoom`s that will override the \
                   :class:`EighthActivity`'s default rooms
        - attendance_taken -- whether the :class:`EighthSponsor` for \
                              the scheduled :class:`EighthActivity` \
                              has taken attendance yet
        - cancelled -- whether the :class:`EighthScheduledActivity` \
                       has been cancelled

    """
    block = models.ForeignKey(EighthBlock)
    activity = models.ForeignKey(EighthActivity)
    members = models.ManyToManyField(User, through="EighthSignup")

    comments = models.TextField(blank=True)

    # Overridden attributes
    sponsors = models.ManyToManyField(EighthSponsor)
    rooms = models.ManyToManyField(EighthRoom)
    capacity = models.SmallIntegerField(null=True)

    attendance_taken = models.BooleanField(default=False)
    cancelled = models.BooleanField(default=False)

    class Meta:
        unique_together = (("block", "activity"),)
        verbose_name_plural = "eighth scheduled activities"

    def __unicode__(self):
        return "{} on {}".format(self.activity.name, self.block)


class EighthSignup(models.Model):
    """Represents a signup/membership in an eighth period activity.

    Attributes:
        - user -- The :class:`User<intranet.apps.users.models.User>`\
                  who has signed up.
        - scheduled_activity -- The :class:`EighthScheduledActivity` for which
                                the user \
                                has signed up.
        - after_deadline -- Whether the signup was after deadline.

    """
    user = models.ForeignKey(User, null=False)
    scheduled_activity = models.ForeignKey(EighthScheduledActivity, null=False, db_index=True)
    after_deadline = models.BooleanField(default=False)

    def validate_unique(self, *args, **kwargs):
        super(EighthSignup, self).validate_unique(*args, **kwargs)

        if self.__class__.objects.exclude(pk=self.pk).filter(user=self.user, scheduled_activity__block=self.scheduled_activity.block):
            raise ValidationError({
                NON_FIELD_ERRORS: ("EighthSignup already exists for the User "
                                   "and the EighthScheduledActivity's block",)
            })

    def __unicode__(self):
        return "{}: {}".format(self.user,
                               self.scheduled_activity.id)

    class Meta:
        unique_together = (("user", "scheduled_activity"),)


class EighthAbsence(models.Model):
    """Represents a user's absence for an eighth period block.

    Attributes:
        - block -- The `EighthBlock` of the absence.
        - user -- The :class:`User<intranet.apps.users.models.User>`\
                  who was absent.

    """
    block = models.ForeignKey(EighthBlock)
    user = models.ForeignKey(User)

    def __unicode__(self):
        return "{}: {}".format(self.user, self.block)

    class Meta:
        unique_together = (("block", "user"),)
