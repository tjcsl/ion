from itertools import chain
import logging
import datetime
from django.db import models
from django.db.models import Q
from django.http import Http404
from django.forms import ModelForm
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
    user = models.ForeignKey(User, null=True)
    first_name = models.CharField(null=True, max_length=63)
    last_name = models.CharField(null=True, max_length=63)
    online_attendance = models.BooleanField(default=True)

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
    # TODO: Capacity should be in ScheduledActivity
    capacity = models.SmallIntegerField(null=False, default=-1)

    unique_together = (("room_number", "name", "capacity"),)

    def __unicode__(self):
        return "{} ({})".format(self.name, self.capacity)


class EighthActivity(models.Model):
    """Represents an eighth period activity.

    Attributes:
        - name -- The name of the activity.
        - sponsors -- The :class:`EighthSponsor`s for the activity.

    """
    # TODO: Add default capacity,
    name = models.CharField(max_length=63)
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
            block_id = self.order_by("date", "block_letter") \
                           .filter(date__gte=now)[0] \
                           .id
        except IndexError:
            block_id = None
        return block_id

    def get_current_blocks(self):
        try:
            block = EighthBlock.objects \
                               .prefetch_related("eighthscheduledactivity_set") \
                               .get(id=self.get_first_upcoming_block())
        except EighthBlock.DoesNotExist:
            # raise Http404
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
                                        through="EighthScheduledActivity", blank=True)

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
        - comment -- notes for the Eighth Office
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
    block = models.ForeignKey(EighthBlock, null=False)
    activity = models.ForeignKey(EighthActivity, null=False, blank=False)
    members = models.ManyToManyField(User, through="EighthSignup")

    comment = models.CharField(max_length=255)

    # Overridden attributes
    sponsors = models.ManyToManyField(EighthSponsor)
    rooms = models.ManyToManyField(EighthRoom)

    attendance_taken = models.BooleanField(default=False)
    cancelled = models.BooleanField(default=False)

    def __unicode__(self):
        return "{} on {}".format(self.activity.name, self.block)


class EighthScheduledActivityForm(ModelForm):
    class Meta:
        model = EighthScheduledActivity
        fields = ['block', 'activity', 'comment', 'sponsors', 'rooms']


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

    def __unicode__(self):
        return "{}: {}".format(self.user,
                               self.scheduled_activity.id)

    # class Meta:
        # unique_together = (("user", "block"),)
        # index_together = [
        #     ["user", "block"],
        #     ["block", "activity"]
        # ]


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
