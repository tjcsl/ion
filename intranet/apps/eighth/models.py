from django.db import models
from intranet.apps.users.models import User


class EighthSponsor(models.Model):
    """Represents a sponsor for an eighth period activity.

    A sponsor could be an actual user or just a name.

    Attributes:
        - user -- A :class:`User<intranet.apps.users.models.User>`\
                  object for the sponsor.
        - name -- A name for the sponsor if there is

    """
    user = models.ForeignKey(User, null=True)
    name = models.CharField(null=True, max_length=63)


class EighthActivity(models.Model):
    """Represents an eighth period activity.

    Attributes:
        - name -- The name of the activity.
        - sponsors -- The EighthSponsors for the activity.

    """
    name = models.CharField(null=False, max_length=63)
    sponsors = models.ManyToManyField(EighthSponsor)

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

    def __unicode__(self):
        return "{}: {}".format(str(self.date), self.block)

    class Meta:
        unique_together = (("date", "block"),)



class EighthScheduledActivity(models.Model):
    block = models.ForeignKey(EighthBlock, null=False)
    activity = models.ForeignKey(EighthActivity, null=False, blank=False)
    members = models.ManyToManyField(User, through="EighthSignup")

    comments = models.CharField(max_length=255)
    # override sponsors
    # override rooms

    attendance_taken = models.BooleanField(null=False, default=False)


class EighthSignup(models.Model):
    """Represents a signup/membership in an eighth period activity.

    Attributes:
        - user -- The :class:`User<intranet.apps.users.models.User>`\
                  who has signed up.
        - block -- The :class:`EighthBlock` of the activity for which \
                   the user has signed up.
        - activity -- The :class:`EighthActivity` for which the user \
                      has signed up.

    """
    user = models.ForeignKey(User, null=False)
    activity = models.ForeignKey(EighthScheduledActivity, null=False)

    def __unicode__(self):
        return "{}: {} ({})".format(self.user,
                                    self.activity,
                                    self.block)

    class Meta:
        unique_together = (("user", "activity"),)


class SignupAlert(models.Model):
    """Stores a user's preferences for signup alerts.

    Description

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

