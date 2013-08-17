import logging
from django.db import models
from django.db.models import Count, Q
from intranet.apps.users.models import User

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


class EighthRoom(models.Model):

    """Represents a room in which an eighth period activity can be held

    Attributes:
        - Attribute -- Description.

    """
    name = models.CharField(max_length=63)
    capacity = models.SmallIntegerField(null=False, default=-1)

    unique_together = (("room_number", "name", "capacity"),)


class EighthActivity(models.Model):

    """Represents an eighth period activity.

    Attributes:
        - name -- The name of the activity.
        - sponsors -- The EighthSponsors for the activity.

    """
    name = models.CharField(max_length=63)
    description = models.TextField()
    sponsors = models.ManyToManyField(EighthSponsor)
    rooms = models.ManyToManyField(EighthRoom)

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


class EighthBlock(models.Model):

    """Represents an eighth period block.

    Attributes:
        - date -- The date of the block.
        - block -- The block letter (e.g. A, B).
        - locked -- Whether signups are closed.
        - activities -- List of \
                        :class:`EighthScheduledActivity` for the block.

    """
    date = models.DateField(null=False)
    block = models.CharField(max_length=1)
    locked = models.BooleanField(default=False)
    activities = models.ManyToManyField(EighthActivity,
                                        through="EighthScheduledActivity")

    def next_blocks(self, quantity=1):
        try:
            return EighthBlock.objects \
                              .order_by("date", "block") \
                              .filter(Q(date__gt=self.date) \
                               | (Q(date=self.date) \
                               & Q(block__gt=self.block)))
        except IndexError:
            return None

    def previous_blocks(self, quantity=1):
        try:
            return EighthBlock.objects \
                              .order_by("-date", "-block") \
                              .filter(Q(date__lt=self.date) \
                               | (Q(date=self.date) \
                               & Q(block__lt=self.block)))
        except IndexError:
            return None

    def __unicode__(self):
        return "{}: {}".format(str(self.date), self.block)

    class Meta:
        unique_together = (("date", "block"),)


class EighthScheduledActivity(models.Model):
    block = models.ForeignKey(EighthBlock, null=False)
    activity = models.ForeignKey(EighthActivity, null=False, blank=False)
    members = models.ManyToManyField(User, through="EighthSignup")

    comment = models.CharField(max_length=255)

    # Overidden attributes
    sponsors = models.ManyToManyField(EighthSponsor)
    rooms = models.ManyToManyField(EighthRoom)

    attendance_taken = models.BooleanField(default=False)
    cancelled = models.BooleanField(default=False)
    room_changed = models.BooleanField(default=False)


class EighthSignup(models.Model):

    """Represents a signup/membership in an eighth period activity.

    Attributes:
        - user -- The :class:`User<intranet.apps.users.models.User>`\
                  who has signed up.
        - activity -- The :class:`EighthScheduledActivity` for which the user \
                      has signed up.

    """
    user = models.ForeignKey(User, null=False)
    activity = models.ForeignKey(EighthScheduledActivity, null=False, db_index=True)
    has_pass = models.BooleanField(default=False)

    def __unicode__(self):
        return "{}: {}".format(self.user,
                               self.activity)

    # class Meta:
        # unique_together = (("user", "block"),)
        # index_together = [
        #     ["user", "block"],
        #     ["block", "activity"]
        # ]


class SignupAlert(models.Model):

    """Stores a user's preferences for signup alerts.

    Attributes:
        - user -- The :class:`User<intranet.apps.users.models.User>`.
        - night_before -- (BOOL) Whether the user wants emails the \
                          night before if he/she hasn't signed up yet
        - day_of -- (BOOL) Whether the user wants emails the day of if \
                    he/she hasn't signed up yet

    """
    user = models.ForeignKey(User, null=False, unique=True)
    night_before = models.BooleanField(null=False)
    day_of = models.BooleanField(null=False)

    def __unicode__(self):
        return "{}: [{}] Night before "\
               "[{}] Day of".format(self.user,
                                    "X" if self.night_before else " ",
                                    "X" if self.day_of else " ")


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
