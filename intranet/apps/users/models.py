# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from base64 import b64encode

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser, PermissionsMixin, UserManager as DjangoUserManager
from django.core.cache import cache
from django.db import models
from django.db.models import Count, F
from django.utils import timezone
from django.utils.functional import cached_property

from intranet.middleware import threadlocals

from ..groups.models import Group
from ..preferences.fields import PhoneField
from ..bus.models import Route

logger = logging.getLogger(__name__)

# TODO: this is disgusting
GRADE_NUMBERS = ((9, 'freshman'), (10, 'sophomore'), (11, 'junior'), (12, 'senior'), (13, 'staff'))


class UserManager(DjangoUserManager):
    """User model Manager for table-level User queries.

    Provides table-level LDAP abstraction for the User model. If a call
    to a method fails for this Manager, the call is deferred to the
    default User model manager.

    """

    def user_with_student_id(self, student_id):
        """Get a unique user object by FCPS student ID. (Ex. 1624472)"""
        results = User.objects.filter(student_id=student_id)
        if len(results) == 1:
            return results.first()
        return None

    def user_with_ion_id(self, student_id):
        """Get a unique user object by Ion ID. (Ex. 489)"""
        if isinstance(student_id, str) and not student_id.isdigit():
            return None
        results = User.objects.filter(id=student_id)
        if len(results) == 1:
            return results.first()
        return None

    def users_in_year(self, year):
        """Get a list of users in a specific graduation year."""
        return User.objects.filter(graduation_year=year)

    def user_with_name(self, given_name=None, sn=None):
        """Get a unique user object by given name (first/nickname and last)."""
        results = []

        if sn and not given_name:
            results = User.objects.filter(last_name=sn)
        elif given_name:
            query = {'first_name': given_name}
            if sn:
                query['last_name'] = sn
            results = User.objects.filter(**query)

            if len(results) == 0:
                # Try their first name as a nickname
                del query['first_name']
                query['nickname'] = given_name
                results = User.objects.filter(**query)

        if len(results) == 1:
            return results.first()

        return None

    def users_with_birthday(self, month, day):
        """Return a list of user objects who have a birthday on a given date."""

        users = User.objects.filter(properties___birthday__month=month, properties___birthday__day=day)
        results = []
        print('=============================')
        for user in users:
            # TODO: permissions system
            print(user.first_name)
            results.append(user)

        return results

    # Simple way to filter out teachers and students without hitting LDAP.
    # This shouldn't be a problem unless the username scheme changes and
    # the consequences of error are not significant.

    def get_students(self):
        """Get user objects that are students (quickly)."""
        return User.objects.filter(user_type="student", graduation_year__gte=settings.SENIOR_GRADUATION_YEAR)

    def get_teachers(self):
        """Get user objects that are teachers (quickly)."""
        users = User.objects.filter(user_type="teacher")
        extra = [9996, 8888, 7011]
        users = users.exclude(id__in=extra)
        # Add possible exceptions handling here
        users = users | User.objects.filter(id__in=[31863, 32327, 32103, 33228])

        return users

    def get_teachers_sorted(self):
        """Get teachers sorted by last name.

        This is used for the announcement request page.

        """
        teachers = self.get_teachers()
        teachers = [(u.last_name, u.first_name, u.id) for u in teachers]
        for t in teachers:
            if t is None or t[0] is None or t[1] is None or t[2] is None:
                teachers.remove(t)
        for t in teachers:
            if t[0] is None or len(t[0]) <= 1:
                teachers.remove(t)
        teachers.sort(key=lambda u: (u[0], u[1]))
        # Hack to return QuerySet in given order
        id_list = [t[2] for t in teachers]
        clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(id_list)])
        ordering = 'CASE %s END' % clauses
        queryset = User.objects.filter(id__in=id_list).extra(select={'ordering': ordering}, order_by=('ordering',))
        return queryset


class User(AbstractBaseUser, PermissionsMixin):
    """Django User model subclass
    """
    TITLES = (('Mr.', 'Mr.'), ('Ms.', 'Ms.'), ('Mrs.', 'Mrs.'), ('Dr.', 'Dr.'))

    USER_TYPES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('counselor', 'Counselor'),
        ('user', 'Attendance-Only User'),
        ('simple_user', 'Simple User'),
        ('tjstar_presenter', 'tjStar Presenter'),
        ('alum', 'Alumnus'),
        ('service', 'Service Account'),
    )

    TITLES = (('mr', 'Mr.'), ('ms', 'Ms.'), ('mrs', 'Mrs.'), ('dr', 'Dr.'))
    # Django Model Fields
    username = models.CharField(max_length=30, unique=True)

    # See Email model for emails
    # See Phone model for phone numbers
    # See Website model for websites

    user_locked = models.BooleanField(default=False)

    # Local internal fields
    first_login = models.DateTimeField(null=True)
    seen_welcome = models.BooleanField(default=False)

    # Local preference fields
    receive_news_emails = models.BooleanField(default=False)
    receive_eighth_emails = models.BooleanField(default=False)

    receive_schedule_notifications = models.BooleanField(default=False)

    student_id = models.CharField(max_length=settings.FCPS_STUDENT_ID_LENGTH, unique=True, null=True)
    user_type = models.CharField(max_length=30, choices=USER_TYPES, default='student')
    admin_comments = models.TextField(blank=True, null=True)
    counselor = models.ForeignKey('self', on_delete=models.SET_NULL, related_name='students', null=True)
    graduation_year = models.IntegerField(null=True)
    title = models.CharField(max_length=5, choices=TITLES, null=True, blank=True)
    first_name = models.CharField(max_length=35, null=True)
    middle_name = models.CharField(max_length=70, null=True)
    last_name = models.CharField(max_length=70, null=True)
    nickname = models.CharField(max_length=35, null=True)
    gender = models.NullBooleanField()
    preferred_photo = models.OneToOneField('Photo', related_name='+', null=True, blank=True, on_delete=models.SET_NULL)
    primary_email = models.OneToOneField('Email', related_name='+', null=True, blank=True, on_delete=models.SET_NULL)
    bus_route = models.ForeignKey(Route, on_delete=models.SET_NULL, null=True)

    # Required to replace the default Django User model
    USERNAME_FIELD = "username"
    """Override default Model Manager (objects) with
    custom UserManager to add table-level functionality."""
    objects = UserManager()

    @staticmethod
    def get_signage_user():
        return User(id=99999)

    @property
    def address(self):
        return self.properties.address

    @property
    def birthday(self):
        return self.properties.birthday

    @property
    def schedule(self):
        return self.properties.schedule

    def member_of(self, group):
        """Returns whether a user is a member of a certain group.

        Args:
            group
                The name of a group (string) or a group object

        Returns:
            Boolean

        """
        if isinstance(group, Group):
            group = group.name
        return self.groups.filter(name=group).exists()

    def has_admin_permission(self, perm):
        """Returns whether a user has an admin permission (explicitly, or implied by being in the
        "admin_all" group)

        Returns:
            Boolean

        """
        return self.member_of("admin_all") or self.member_of("admin_" + perm)

    @property
    def full_name(self):
        """Return full name, e.g. Angela William.

        This is required for subclasses of User.

        """
        return "{} {}".format(self.first_name, self.last_name)

    @property
    def display_name(self):
        return self.full_name

    @property
    def last_first(self):
        """Return a name in the format of:
            Lastname, Firstname [(Nickname)]
        """
        return "{}, {} ".format(self.last_name, self.first_name) + ("({})".format(self.nickname) if self.nickname else "")

    @property
    def last_first_id(self):
        """Return a name in the format of:
            Lastname, Firstname [(Nickname)] (Student ID/ID/Username)
        """
        return ("{}{} ".format(self.last_name, ", " + self.first_name if self.first_name else "") + ("({}) ".format(self.nickname)
                                                                                                     if self.nickname else "") +
                ("({})".format(self.student_id if self.is_student and self.student_id else self.username)))

    @property
    def last_first_initial(self):
        """Return a name in the format of:
            Lastname, F [(Nickname)]
        """
        return ("{}{} ".format(self.last_name, ", " + self.first_name[:1] + "." if self.first_name else "") + ("({}) ".format(self.nickname)
                                                                                                               if self.nickname else ""))

    @property
    def short_name(self):
        """Return short name (first name) of a user.

        This is required for subclasses of User.

        """
        return self.first_name

    def get_short_name(self):
        """Get short (first) name of a user."""
        return self.short_name

    @property
    def tj_email(self):
        """Get (or guess) a user's TJ email.

        If a fcps.edu or tjhsst.edu email is specified in their email
        list, use that. Otherwise, append the user's username to the
        proper email suffix, depending on whether they are a student or
        teacher.

        """

        for email in self.emails.all():
            if email.address.endswith(("@fcps.edu", "@tjhsst.edu")):
                return email

        if self.is_teacher:
            domain = "fcps.edu"
        else:
            domain = "tjhsst.edu"

        return "{}@{}".format(self.username, domain)

    @property
    def default_photo(self):
        """Returns default photo (in binary) that should be used

        Returns:
            Binary data

        """
        preferred = self.preferred_photo
        if preferred is not None:
            return preferred.binary

        if preferred is None:
            if self.user_type == "teacher":
                current_grade = 12
            else:
                current_grade = int(self.grade)
                if current_grade > 12:
                    current_grade = 12
            for i in reversed(range(9, current_grade + 1)):
                data = None
                if self.photos.filter(grade_number=i).exists():
                    data = self.photos.filter(grade_number=i).first().binary
                if data:
                    return data

    @property
    def grade(self):
        """Returns the grade of a user.

        Returns:
            Grade object

        """
        return Grade(self.graduation_year)

    @property
    def permissions(self):
        """Dynamically generate dictionary of privacy options
        """
        # TODO: optimize this, it's kind of a bad solution for listing a mostly
        # static set of files.
        # We could either add a permissions dict as an attribute or cache this
        # in some way. Creating a dict would be another place we have to define
        # the permission, so I'm not a huge fan, but it would definitely be the
        # easier option.
        permissions_dict = {"self": {}, "parent": {}}

        for field in self.properties._meta.get_fields():
            split_field = field.name.split('_', 1)
            if len(split_field) <= 0 or split_field[0] not in ['self', 'parent']:
                continue
            permissions_dict[split_field[0]][split_field[1]] = getattr(self.properties, field.name)

        return permissions_dict

    def _current_user_override(self):
        """Return whether the currently logged in user is a teacher, and can view all of a student's
        information regardless of their privacy settings."""
        try:
            # threadlocals is a module, not an actual thread locals object
            request = threadlocals.request()
            if request is None:
                return False
            requesting_user = request.user
            if isinstance(requesting_user, AnonymousUser) or not requesting_user.is_authenticated:
                return False
            can_view_anyway = requesting_user and (requesting_user.is_teacher or requesting_user.is_eighthoffice or requesting_user.is_eighth_admin)
        except (AttributeError, KeyError) as e:
            logger.error("Could not check teacher/eighth override: {}".format(e))
            can_view_anyway = False
        return can_view_anyway

    @property
    def ion_username(self):
        return self.username

    @property
    def grade_number(self):
        return self.grade.number

    @property
    def sex(self):
        return "Male" if self.is_male else "Female"

    @property
    def is_male(self):
        return self.gender is True

    @property
    def is_female(self):
        return self.gender is False

    @property
    def age(self):
        """Returns a user's age, based on their birthday.

        Returns:
            integer

        """
        date = datetime.today().date()

        b = self.birthday
        if b:
            return int((date - b).days / 365)

        return None

    @property
    def can_view_eighth(self):
        """Checks if a user has the show_eighth permission.

        Returns:
            Boolean

        """

        return self.properties.attribute_is_visible("show_eighth")

    @property
    def is_eighth_admin(self):
        """Checks if user is an eighth period admin.

        Returns:
            Boolean

        """

        return self.has_admin_permission('eighth')

    @property
    def has_print_permission(self):
        """Checks if user has the admin permission 'printing'.

        Returns:
            Boolean

        """

        return self.has_admin_permission('printing')

    @property
    def is_parking_admin(self):
        """Checks if user has the admin permission 'parking'.

        Returns:
            Boolean

        """

        return self.has_admin_permission('parking')

    @property
    def can_request_parking(self):
        """Checks if user can view the parking interface.

        Returns:
            Boolean

        """
        return self.grade_number >= 11 or self.is_parking_admin

    @property
    def is_announcements_admin(self):
        """Checks if user is an announcements admin.

        Returns:
            Boolean

        """

        return self.has_admin_permission("announcements")

    @property
    def is_schedule_admin(self):
        """Checks if user is a schedule admin.

        Returns:
            Boolean

        """

        return self.has_admin_permission("schedule")

    @property
    def is_board_admin(self):
        """Checks if user is a board admin.

        Returns:
            Boolean

        """

        return self.has_admin_permission("board")

    @property
    def is_teacher(self):
        """Checks if user is a teacher.

        Returns:
            Boolean

        """
        return self.user_type == "teacher" or self.user_type == "counselor"

    @property
    def is_student(self):
        """Checks if user is a student.

        Returns:
            Boolean

        """
        return self.user_type == "student"

    @property
    def is_alum(self):
        """Checks if user is an alumnus.

        Returns:
            Boolean

        """
        return self.user_type == "alum"

    @property
    def is_senior(self):
        """Checks if user is a student in Grade 12.

        Returns:
            Boolean

        """
        return self.is_student and self.grade_number == 12

    @property
    def is_eighthoffice(self):
        """Checks if user is an Eighth Period office user.

        This is currently hardcoded, but is meant to be used instead
        of user.id == 9999 or user.username == "eighthoffice".

        Returns:
            Boolean

        """
        return self.id == 9999

    @property
    def is_active(self):
        """Checks if the user is active.

        This is currently used to catch invalid logins.

        """

        return not self.username.startswith("INVALID_USER") and not self.user_locked

    @property
    def is_restricted(self):
        """Checks if user needs the restricted view of Ion

        This applies to users that are user_type 'user', user_type 'alum'
        or user_type 'service'

        """

        return self.user_type in ['user', 'alum', 'service']

    @property
    def is_staff(self):
        """Checks if a user should have access to the Django Admin interface.

        This has nothing to do with staff at TJ - `is_staff`
        has to be overridden to make this a valid user model.

        Returns:
            Boolean

        """

        return self.is_superuser or self.has_admin_permission("staff")

    @property
    def is_attendance_user(self):
        """Checks if user is an attendance-only user.

        Returns:
            Boolean

        """
        return self.user_type == "user"

    @property
    def is_simple_user(self):
        """Checks if user is a simple user (e.g. eighth office user)

        Returns:
            Boolean

        """
        return self.user_type == "simple_user"

    @property
    def male(self):
        """Return if the user is male."""
        return self.is_male

    @property
    def female(self):
        """Return if the user is female."""
        return self.is_female

    @property
    def has_senior(self):
        try:
            self.senior
        except AttributeError:
            return False
        return True

    @property
    def is_attendance_taker(self):
        """Checks if user can take attendance for an eighth activity.

        Returns:
            Boolean

        """
        return self.is_eighth_admin or self.is_teacher or self.is_attendance_user

    @property
    def is_eighth_sponsor(self):
        """Determine whether the given user is associated with an.

        :class:`intranet.apps.eighth.models.EighthSponsor` and, therefore, should view activity
        sponsoring information.

        """
        # FIXME: remove recursive dep
        from ..eighth.models import EighthSponsor

        return EighthSponsor.objects.filter(user=self).exists()

    @property
    def startpage(self):
        return "eighth" if self.is_simple_user else None

    @property
    def frequent_signups(self):
        """Return a QuerySet of activity id's and counts for the activities that a given user
        has signed up for more than `settings.SIMILAR_THRESHOLD` times"""
        key = "{}:frequent_signups".format(self.username)
        cached = cache.get(key)
        if cached:
            return cached
        freq_signups = self.eighthsignup_set.exclude(scheduled_activity__activity__administrative=True).exclude(
            scheduled_activity__activity__special=True).exclude(scheduled_activity__activity__restricted=True).exclude(
                scheduled_activity__activity__deleted=True).values('scheduled_activity__activity').annotate(
                    count=Count('scheduled_activity__activity')).filter(count__gte=settings.SIMILAR_THRESHOLD).order_by('-count')
        cache.set(key, freq_signups, timeout=60 * 60 * 24 * 7)
        return freq_signups

    @property
    def recommended_activities(self):
        key = "{}:recommended_activities".format(self.username)
        cached = cache.get(key)
        if cached:
            return cached
        acts = set()
        for signup in self.eighthsignup_set.exclude(scheduled_activity__activity__administrative=True).exclude(
                scheduled_activity__activity__special=True).exclude(scheduled_activity__activity__restricted=True).exclude(
                    scheduled_activity__activity__deleted=True).exclude(
                        scheduled_activity__block__date__lte=(datetime.now() + relativedelta(months=-6))):
            acts.add(signup.scheduled_activity.activity)
        close_acts = set()
        for act in acts:
            sim = act.similarities.order_by('-weighted').first()
            if sim and sim.weighted > 1:
                close_acts.add(sim.activity_set.exclude(id=act.id).first())
        cache.set(key, close_acts, timeout=60 * 60 * 24 * 7)
        return close_acts

    def archive_admin_comments(self):
        current_year = datetime.now().year
        previous_year = current_year - 1
        self.admin_comments = "\n=== {}-{} comments ===\n{}".format(previous_year, current_year, self.admin_comments)
        self.save()

    def get_eighth_sponsor(self):
        """Return the :class:`intranet.apps.eighth.models.EighthSponsor` that a given user is
        associated with.
        """

        # FIXME: remove recursive dep
        from ..eighth.models import EighthSponsor

        try:
            sp = EighthSponsor.objects.get(user=self)
        except EighthSponsor.DoesNotExist:
            return False

        return sp

    def has_unvoted_polls(self):
        # FIXME: remove recursive dep
        from ..polls.models import Poll, Answer

        now = timezone.now()
        for poll in Poll.objects.visible_to_user(self).filter(start_time__lt=now, end_time__gt=now):
            if Answer.objects.filter(question__in=poll.question_set.all(), user=self).count() == 0:
                return True

        return False

    def signed_up_today(self):
        # FIXME: remove recursive dep
        from ..eighth.models import EighthBlock, EighthSignup

        if not self.is_student:
            return True

        for b in EighthBlock.objects.get_upcoming_blocks(2):
            if b.is_today() and not EighthSignup.objects.filter(user=self, scheduled_activity__block=b).count():
                return False

        return True

    def absence_count(self):
        """Return the user's absence count.

        If the user has no absences
        or is not a signup user, returns 0.

        """
        # FIXME: remove recursive dep
        from ..eighth.models import EighthSignup

        return EighthSignup.objects.filter(user=self, was_absent=True, scheduled_activity__attendance_taken=True).count()

    def absence_info(self):
        """Return information about the user's absences."""
        # FIXME: remove recursive dep
        from ..eighth.models import EighthSignup

        return EighthSignup.objects.filter(user=self, was_absent=True, scheduled_activity__attendance_taken=True)

    def handle_delete(self):
        """Handle a graduated user being deleted."""
        from intranet.apps.eighth.models import EighthScheduledActivity
        EighthScheduledActivity.objects.filter(eighthsignup_set__user=self).update(
                archived_member_count=F('archived_member_count')+1)

    def __getattr__(self, name):
        if name == "properties":
            return UserProperties.objects.get_or_create(user=self)[0]
        raise AttributeError

    def __str__(self):
        return self.username or self.ion_username or self.id

    def __int__(self):
        return self.id


class UserProperties(models.Model):
    user = models.OneToOneField('User', related_name="properties", on_delete=models.CASCADE)

    _address = models.OneToOneField('Address', null=True, blank=True, on_delete=models.SET_NULL)
    _birthday = models.DateField(null=True)
    _schedule = models.ManyToManyField('Section', related_name='_students')
    """ User preference permissions (privacy options)
        When setting permissions, use set_permission(permission, value , parent=False)
        The permission attribute should be the part after "self_" or "parent_"
            e.g. show_pictures
        If you're setting permission of the student, but the parent permission is false,
        the method will fail and return False.

        To define a new permission, just create two new BooleanFields in the same
        pattern as below.
    """
    self_show_pictures = models.BooleanField(default=False)
    parent_show_pictures = models.BooleanField(default=False)

    self_show_address = models.BooleanField(default=False)
    parent_show_address = models.BooleanField(default=False)

    self_show_telephone = models.BooleanField(default=False)
    parent_show_telephone = models.BooleanField(default=False)

    self_show_birthday = models.BooleanField(default=False)
    parent_show_birthday = models.BooleanField(default=False)

    self_show_eighth = models.BooleanField(default=False)
    parent_show_eighth = models.BooleanField(default=False)

    self_show_schedule = models.BooleanField(default=False)
    parent_show_schedule = models.BooleanField(default=False)

    def __getattr__(self, name):
        if name.startswith("self") or name.startswith("parent"):
            return object.__getattribute__(self, name)
        if name == "address":
            return self._address if self.attribute_is_visible("show_address") else None
        if name == "birthday":
            return self._birthday if self.attribute_is_visible("show_birthday") else None
        if name == "schedule":
            return self._schedule if self.attribute_is_visible("show_schedule") else None
        raise AttributeError

    def __setattr__(self, name, value):
        if name == "address":
            if self.attribute_is_visible("show_address"):
                self._address = value
        if name == "birthday":
            if self.attribute_is_visible("show_birthday"):
                self._birthday = value
        super(UserProperties, self).__setattr__(name, value)

    def __str__(self):
        return self.user.__str__()

    def set_permission(self, permission, value, parent=False, admin=False):
        """ Sets permission for personal information.
            Returns False silently if unable to set permission.
            Returns True if successful.
        """
        try:
            if not getattr(self, 'parent_{}'.format(permission)) and not parent and not admin:
                return False
            level = 'parent' if parent else 'self'
            setattr(self, '{}_{}'.format(level, permission), value)

            # Set student permission to false if parent sets permission to false.
            if parent and not value:
                setattr(self, 'self_{}'.format(permission), False)

            self.save()
            return True
        except Exception as e:
            logger.error("Error occurred setting permission {} to {}: {}".format(permission, value, e))
            return False

    def _current_user_override(self):
        """Return whether the currently logged in user is a teacher, and can view all of a student's
        information regardless of their privacy settings."""
        try:
            # threadlocals is a module, not an actual thread locals object
            request = threadlocals.request()
            if request is None:
                return False
            requesting_user = request.user
            if isinstance(requesting_user, AnonymousUser) or not requesting_user.is_authenticated:
                return False
            can_view_anyway = requesting_user and (requesting_user.is_teacher or requesting_user.is_eighthoffice or requesting_user.is_eighth_admin)
        except (AttributeError, KeyError) as e:
            logger.error("Could not check teacher/eighth override: {}".format(e))
            can_view_anyway = False
        return can_view_anyway

    def is_http_request_sender(self):
        """Checks if a user the HTTP request sender (accessing own info)

        Used primarily to load private personal information from the
        cache. (A student should see all info on his or her own profile
        regardless of how the permissions are set.)

        Returns:
            Boolean

        """
        try:
            # threadlocals is a module, not an actual thread locals object
            request = threadlocals.request()
            if request and request.user and request.user.is_authenticated:
                requesting_user_id = request.user.id
                return str(requesting_user_id) == str(self.user.id)
        except (AttributeError, KeyError) as e:
            logger.error("Could not check request sender: {}".format(e))
            return False

        return False

    def attribute_is_visible(self, permission):
        """ Checks privacy options to see if an attribute is visible to public
        """
        try:
            parent = getattr(self, "parent_{}".format(permission))
            student = getattr(self, "self_{}".format(permission))
            return (parent and student) or (self.is_http_request_sender() or self._current_user_override())
        except Exception:
            logger.error("Could not retrieve permissions for {}".format(permission))

    def attribute_is_public(self, permission):
        """ Checks if attribute is visible to public (regardless of admins status)
        """
        try:
            parent = getattr(self, "parent_{}".format(permission))
            student = getattr(self, "self_{}".format(permission))
            return (parent and student)
        except Exception:
            logger.error("Could not retrieve permissions for {}".format(permission))


class Email(models.Model):
    """Represents an email address"""
    address = models.EmailField()
    user = models.ForeignKey(User, related_name='emails', on_delete=models.CASCADE)

    def __str__(self):
        return self.address

    class Meta:
        unique_together = ('user', 'address')


class Phone(models.Model):
    """Represents a phone number"""
    PURPOSES = (('h', 'Home Phone'), ('m', 'Mobile Phone'), ('o', 'Other Phone'))

    purpose = models.CharField(max_length=1, choices=PURPOSES, default='o')
    user = models.ForeignKey(User, related_name='phones', on_delete=models.CASCADE)
    _number = PhoneField()  # validators should be a list

    def __setattr__(self, name, value):
        if name == "number":
            if self.user.properties.attribute_is_visible("show_telephone"):
                self._number = value
                self.save()
        else:
            super(Phone, self).__setattr__(name, value)

    def __getattr__(self, name):
        if name == "number":
            return self._number if self.user.properties.attribute_is_visible("show_telephone") else None
        raise AttributeError

    def __str__(self):
        return "{}: {}".format(self.get_purpose_display(), self.number)

    class Meta:
        unique_together = ('user', '_number')


class Website(models.Model):
    """Represents a user's website"""
    url = models.URLField()
    user = models.ForeignKey(User, related_name='websites', on_delete=models.CASCADE)

    def __str__(self):
        return self.url

    class Meta:
        unique_together = ('user', 'url')


class Address(models.Model):
    """Represents a user's address.

    Attributes:
        street
            The street name of the address.
        city
            The city name of the address.
        state
            The state name of the address.
        postal_code
            The zip code of the address.

    """

    street = models.CharField(max_length=255)
    city = models.CharField(max_length=40)
    state = models.CharField(max_length=20)
    postal_code = models.CharField(max_length=20)

    def __str__(self):
        """Returns full address string."""
        return "{}\n{}, {} {}".format(self.street, self.city, self.state, self.postal_code)


class Photo(models.Model):
    """Represents a user photo"""

    grade_number = models.IntegerField(choices=GRADE_NUMBERS)
    _binary = models.BinaryField()
    user = models.ForeignKey(User, related_name="photos", on_delete=models.CASCADE)

    def __setattr__(self, name, value):
        if name == "binary":
            if self.user.properties.attribute_is_visible("show_pictures"):
                self._binary = value
                self.save()
        else:
            super(Photo, self).__setattr__(name, value)

    def __getattr__(self, name):
        if name == "binary":
            return self._binary if self.user.properties.attribute_is_visible("show_pictures") else None
        raise AttributeError

    @cached_property
    def base64(self):
        """Returns base64 encoded binary data for a user's picture.

        Returns:
           Base64 string, or None
        """

        binary = self.binary
        if binary:
            return b64encode(binary)
        return None


class Grade(object):
    """Represents a user's grade."""
    names = ["freshman", "sophomore", "junior", "senior"]

    def __init__(self, graduation_year):
        """Initialize the Grade object.

        Args:
            graduation_year
                The numerical graduation year of the user

        """
        if graduation_year is None:
            self._number = 13
        else:
            self._number = settings.SENIOR_GRADUATION_YEAR - int(graduation_year) + 12

        if 9 <= self._number <= 12:
            self._name = Grade.names[self._number - 9]
        else:
            self._name = "graduate"

    @property
    def number(self):
        """Return the grade as a number (9-12).

        For use in templates since there is no nice integer casting.
        In Python code you can also use int() on a Grade object.

        """
        return self._number

    @property
    def name(self):
        """Return the grade's name (e.g. senior)"""
        return self._name

    @property
    def name_plural(self):
        """Return the grade's plural name (e.g. freshmen)"""
        return "freshmen" if (self._number and self._number == 9) else "{}s".format(self._name) if self._name else ""

    @property
    def text(self):
        """Return the grade's number as a string (e.g. Grade 12, Graduate)"""
        if 9 <= self._number <= 12:
            return "Grade {}".format(self._number)
        else:
            return self._name

    @staticmethod
    def number_from_name(name):
        if name in Grade.names:
            return Grade.names.index(name) + 9
        return None

    @classmethod
    def grade_from_year(cls, graduation_year):
        today = datetime.now()
        if today.month >= settings.YEAR_TURNOVER_MONTH:
            current_senior_year = today.year + 1
        else:
            current_senior_year = today.year

        return current_senior_year - graduation_year + 12

    @classmethod
    def year_from_grade(cls, grade):
        today = datetime.now()
        if today.month >= settings.YEAR_TURNOVER_MONTH:
            current_senior_year = today.year + 1
        else:
            current_senior_year = today.year

        return current_senior_year + 12 - grade

    def __int__(self):
        """Return the grade as a number (9-12)."""
        return self._number

    def __str__(self):
        """Return name of the grade."""
        return self._name


class Course(models.Model):
    """Represents a course at TJ (not to be confused with section)"""

    name = models.CharField(max_length=50)
    course_id = models.CharField(max_length=12, unique=True)

    def __str__(self):
        return "{} ({})".format(self.name, self.course_id)


class Section(models.Model):
    """Represents a section - a class with teacher, period, and room assignments"""

    course = models.ForeignKey(Course, related_name="sections", on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    room = models.CharField(max_length=16)
    period = models.IntegerField()
    section_id = models.CharField(max_length=16, unique=True)
    sem = models.CharField(max_length=2)

    def __str__(self):
        return "{} ({}) - {} Pd. {}".format(self.course.name, self.section_id, self.teacher.full_name if self.teacher else "Unknown", self.period)

    def __getattr__(self, name):
        if name == "students":
            return [s.user for s in self._students.all() if s.attribute_is_visible("show_schedule")]
        raise AttributeError
