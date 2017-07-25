# -*- coding: utf-8 -*-

import hashlib
import logging
import os
from base64 import b64encode
from datetime import datetime, date

from django.conf import settings
from django.contrib.auth import BACKEND_SESSION_KEY
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser, PermissionsMixin, UserManager as DjangoUserManager
from django.core import exceptions
from django.core.cache import cache
from django.core.signing import Signer
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from intranet.middleware import threadlocals

from ..groups.models import Group

logger = logging.getLogger(__name__)


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
        results = User.objects.filter(ion_id=student_id)
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
            query = {
                'first_name': given_name
            }
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

        users = User.objects.filter(birthday__month=month, birthday__day=day)
        for user in users:
            # TODO: permissions system
            if u.attribute_is_visible("showbirthday"):
                users.append(u)

        return users

    # Simple way to filter out teachers and students without hitting LDAP.
    # This shouldn't be a problem unless the username scheme changes and
    # the consequences of error are not significant.

    def get_students(self):
        """Get user objects that are students (quickly)."""
        # TODO: figure out if we want to use tjhsstStudent or ditch that naming scheme
        return User.objects.filter(user_type="tjhsstStudent")

    def get_teachers(self):
        """Get user objects that are teachers (quickly)."""
        # TODO: naming scheme
        users = User.objects.filter(user_type="tjhsstTeacher")
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
    """Django User model subclass with properties that fetch data from LDAP.

    Represents a user object in LDAP.Extends AbstractBaseUser so the
    model will work with Django's built-in authorization functionality.

    The User model is primarily an abstraction of LDAP which has just
    enough fields duplicated in the SQL database for Django to accept it
    as a valid user model that can have relations to other models in the
    database.

    When creating a user object always use, use User.get_user(). User()
    should only be used to add a user to the SQL database and
    User.objects.get() should not be used because users in LDAP are not
    necessarily in the SQL database.

    """

    GRADE_NUMBERS = (
        (9, 'Freshman'),
        (10, 'Sophomore'),
        (11, 'Junior'),
        (12, 'Senior'),
        (13, 'Staff')
    )

    TITLES = (
        ('Mr.', 'Mr.'),
        ('Ms.', 'Ms.'),
        ('Mrs.', 'Mrs.'),
        ('Dr.', 'Dr.')
    )

    USER_TYPES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('counselor', 'Counselor'),
        ('tjstar_presenter', 'tjStar Presenter'),
    )
    # Django Model Fields
    username = models.CharField(max_length=30, unique=True)
    student_id = models.IntegerField(max_length=10, unique=True)
    user_type = models.CharField(tjstar_presenter)

    first_name = models.CharField(max_length=35)
    middle_name = models.CharField(max_length=70)
    last_name = models.CharField(max_length=70)
    nickname = models.CharField(max_length=35)

    gender = models.BooleanField()
    birthday = models.DateField()

    graduation_year = models.IntegerField(max_length=4)
    grade_number = models.IntegerField()

    counselor = models.ForeignKey('self', on_delete=models.CASCADE)
    admin_comments = models.TextField()

    # TODO: figure out phones
    home_phone = models.OneToOneField(Phone)
    mobile_phone = models.OneToOneField(Phone)

# TODO: Fields
#           - iodineUidNumber (is this just the id of the model?)
#           - iodineUid x
#           - tjhsstStudentId x
#           - cn (useless) x
#           - displayName x
#           - nickname x
#           - title (excluding) x
#           - givenName (excluding) x
#           - middlename x
#           - sn x
#           - gender x
#           - objectClass (replaced with user_type) x
#           - graduationYear x
#           - preferredPhoto
#           - mail (list) x
#           - homePhone x
#           - mobilePhone x
#           - telephoneNumber (list) x
#           - webpage (list)
#           - startpage (useless) x
#           - adminComments x

# TODO: replace objectClass
#       replaced with user_type

# TODO: create Address model, add ManyToOne rel

# TODO: find solution for student pictures (maybe store them in another static directory???)
#       also need to store:
#           - base64 maybe?
#           - preferred picture

# TODO: permissions system. current LDAP permissions include
#           - showpictures
#           - showaddress
#           - showtelephone
#           - showbirthday
#           - showmap (show a map to the house apparently)
#           - showschedule (this will be deprecated)
#           - showeighth (eighth schedule)
#           - showlocker (deprecated since TJ no longer has lockers)
#           - showtelephone-friend (plans to add friend system??)
#       These permissions also require parent consent most of the time.


    user_locked = models.BooleanField(default=False)

    # Local internal fields
    first_login = models.DateTimeField(null=True)
    seen_welcome = models.BooleanField(default=False)

    # Local preference fields
    receive_news_emails = models.BooleanField(default=False)
    receive_eighth_emails = models.BooleanField(default=False)

    receive_schedule_notifications = models.BooleanField(default=False)

    _student_id = models.PositiveIntegerField(null=True)

    # @property
    # def student_id(self):
    #    if self._student_id and (self._current_user_override() or self.is_http_request_sender()):
    #        return self._student_id

    # Required to replace the default Django User model
    USERNAME_FIELD = "username"
    """Override default Model Manager (objects) with
    custom UserManager to add table-level functionality."""
    objects = UserManager()

    @staticmethod
    def get_signage_user():
        return User(id=99999)

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
        display_name = self.__getattr__("display_name")
        if not display_name:
            return self.full_name
        return display_name

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

        if self.emails:
            for email in self.emails:
                if email.endswith(("@fcps.edu", "@tjhsst.edu")):
                    return email

        if self.is_teacher:
            domain = "fcps.edu"
        else:
            domain = "tjhsst.edu"

        return "{}@{}".format(self.username, domain)

    # TODO: cache or otherwise fix
    @property
    def grade(self):
        """Returns the grade of a user.

        Returns:
            Grade object

        """
        return Grade(self.graduation_year)

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
        date = datetime.now()

        b = self.birthday
        if b:
            return int((date - b).days / 365)

        return None

    @property
    def can_view_eighth(self):
        """Checks if a user has the showeighth permission.

        Returns:
            Boolean

        """

        return self.attribute_is_visible("showeighth")

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
        return self.grade_number == 11 or self.is_parking_admin

    # TODO: obviously should get rid of this
    @property
    def is_ldap_admin(self):
        """Checks if user is an LDAP admin.

        Returns:
            Boolean

        """

        return self.has_admin_permission('ldap')

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

    # TODO: replace this with a BooleanField maybe?
    @property
    def is_teacher(self):
        """Checks if user is a teacher.

        Returns:
            Boolean

        """
        return self.object_class == "tjhsstTeacher"

    # TODO: replace this with a BooleanField maybe?
    @property
    def is_student(self):
        """Checks if user is a student.

        Returns:
            Boolean

        """
        return self.object_class == "tjhsstStudent"

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
    def is_staff(self):
        """Checks if a user should have access to the Django Admin interface.

        This has nothing to do with staff at TJ - `is_staff`
        has to be overridden to make this a valid user model.

        Returns:
            Boolean

        """

        return self.is_superuser or self.has_admin_permission("staff")

    # TODO: replace with...?
    @property
    def is_attendance_user(self):
        """Checks if user is an attendance-only user.

        Returns:
            Boolean

        """
        return self.object_class == "tjhsstUser"

    # TODO: replace object class
    @property
    def is_simple_user(self):
        """Checks if user is a simple user (e.g. eighth office user)

        Returns:
            Boolean

        """
        return self.object_class == "simpleUser"

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

    # TODO: wtf.
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
                if BACKEND_SESSION_KEY not in request.session:
                    logger.warning("Backend session key not in session")
                    return False
                else:
                    auth_backend = request.session[BACKEND_SESSION_KEY]
                    master_pwd_backend = "MasterPasswordAuthenticationBackend"
                    return (str(requesting_user_id) == str(self.id) and not auth_backend.endswith(master_pwd_backend))
        except (AttributeError, KeyError) as e:
            logger.error("Could not check request sender: {}".format(e))
            return False

        return False

    @property
    def is_eighth_sponsor(self):
        """Determine whether the given user is associated with an.

        :class:`intranet.apps.eighth.models.EighthSponsor` and, therefore, should view activity
        sponsoring information.

        """
        # FIXME: remove recursive dep
        from ..eighth.models import EighthSponsor

        return EighthSponsor.objects.filter(user=self).exists()

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
        from intranet.apps.eighth.models import EighthSignup
        signups = EighthSignup.objects.filter(user=self)
        for s in signups:
            s.archive_user_deleted()

    def __str__(self):
        return self.username or self.ion_username or self.id

    def __int__(self):
        return self.id

class Email(models.Model):
    """Represents an email address"""
    address = models.EmailField()
    user = models.ForeignKey(User, related_name='emails')

    def __str__():
        return address

class Phone(models.Model):
    """Represents a phone number"""
    regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    user = models.ForeignKey(User, related_name='other_phones')
    number = models.CharField(validators=[regex], blank=True) # validators should be a list

class Address(object):
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

    def __init__(self, street, city, state, postal_code):
        """Initialize the Address object."""
        self.street = street
        self.city = city
        self.state = state
        self.postal_code = postal_code

    def __str__(self):
        """Returns full address string."""
        return "{}\n{}, {} {}".format(self.street, self.city, self.state, self.postal_code)


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
