# pylint: disable=too-many-lines; Allow more than 1000 lines
import logging
from base64 import b64encode
from datetime import timedelta
from typing import Collection, Dict, Optional, Union

from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser, PermissionsMixin
from django.contrib.auth.models import UserManager as DjangoUserManager
from django.core.cache import cache
from django.db import models
from django.db.models import Count, F, Q, QuerySet
from django.utils import timezone
from django.utils.functional import cached_property

from intranet.middleware import threadlocals

from ...utils.date import get_senior_graduation_year
from ...utils.helpers import is_entirely_digit
from ..bus.models import Route
from ..eighth.models import EighthBlock, EighthSignup, EighthSponsor
from ..groups.models import Group
from ..polls.models import Poll
from ..preferences.fields import PhoneField

logger = logging.getLogger(__name__)

# TODO: this is disgusting
GRADE_NUMBERS = ((9, "freshman"), (10, "sophomore"), (11, "junior"), (12, "senior"), (13, "staff"))
# Eighth Office/Demo Student user IDs that should be excluded from teacher/student lists
EXTRA = [9996, 8888, 7011]


class UserManager(DjangoUserManager):
    """User model Manager for table-level User queries.

    Provides an abstraction for the User model. If a call
    to a method fails for this Manager, the call is deferred to the
    default User model manager.

    """

    def user_with_student_id(self, student_id: Union[int, str]) -> Optional["User"]:
        """Get a unique user object by FCPS student ID. (Ex. 1624472)"""
        results = User.objects.filter(student_id=str(student_id))
        if len(results) == 1:
            return results.first()
        return None

    def user_with_ion_id(self, student_id: Union[int, str]) -> Optional["User"]:
        """Get a unique user object by Ion ID. (Ex. 489)"""
        if isinstance(student_id, str) and not is_entirely_digit(student_id):
            return None
        results = User.objects.filter(id=str(student_id))
        if len(results) == 1:
            return results.first()
        return None

    def users_in_year(self, year: int) -> Union[Collection["User"], QuerySet]:  # pylint: disable=unsubscriptable-object
        """Get a list of users in a specific graduation year."""
        return User.objects.filter(graduation_year=year)

    def user_with_name(self, given_name: Optional[str] = None, last_name: Optional[str] = None) -> "User":  # pylint: disable=unsubscriptable-object
        """Get a unique user object by given name (first/nickname) and/or last name.

        Args:
            given_name: If given, users will be filtered to those who have either this first name or this nickname.
            last_name: If given, users will be filtered to those who have this last name.

        Returns:
            The unique user object returned by filtering for the given first name/nickname and/or last name. Returns ``None`` if no results were
            returned or if the given parameters matched more than one user.

        """
        results = User.objects.all()

        if last_name:
            results = results.filter(last_name=last_name)
        if given_name:
            results = results.filter(Q(first_name=given_name) | Q(nickname=given_name))

        try:
            return results.get()
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            return None

    def get_students(self) -> Union[Collection["User"], QuerySet]:  # pylint: disable=unsubscriptable-object
        """Get user objects that are students (quickly)."""
        users = User.objects.filter(user_type="student", graduation_year__gte=get_senior_graduation_year())
        users = users.exclude(id__in=EXTRA)

        return users

    def get_teachers(self) -> Union[Collection["User"], QuerySet]:  # pylint: disable=unsubscriptable-object
        """Get user objects that are teachers (quickly)."""
        users = User.objects.filter(user_type="teacher")
        users = users.exclude(id__in=EXTRA)
        # Add possible exceptions handling here
        users = users | User.objects.filter(id__in=[31863, 32327, 32103, 33228])

        users = users.exclude(Q(first_name=None) | Q(first_name="") | Q(last_name=None) | Q(last_name=""))

        return users

    def get_teachers_attendance_users(self) -> "QuerySet[User]":  # noqa
        """Like ``get_teachers()``, but includes attendance-only users as well as
        teachers.

        Returns:
            A QuerySet of users who are either teachers or attendance-only users.

        """
        users = User.objects.filter(user_type__in=["teacher", "user"])
        users = users.exclude(id__in=EXTRA)
        # Add possible exceptions handling here
        users = users | User.objects.filter(id__in=[31863, 32327, 32103, 33228])

        users = users.exclude(Q(first_name=None) | Q(first_name="") | Q(last_name=None) | Q(last_name=""))

        return users

    def get_teachers_sorted(self) -> Union[Collection["User"], QuerySet]:  # pylint: disable=unsubscriptable-object
        """Returns a ``QuerySet`` of teachers sorted by last name, then first name.

        Returns:
            A ``QuerySet`` of teachers sorted by last name, then first name.

        """
        return self.get_teachers().order_by("last_name", "first_name")

    def get_teachers_attendance_users_sorted(self) -> "QuerySet[User]":  # noqa
        """Returns a ``QuerySet`` containing both teachers and attendance-only users sorted by
        last name, then first name.

        This is used for the announcement request page.

        Returns:
            A ``QuerySet`` of teachers sorted by last name, then first name.

        """
        return self.get_teachers_attendance_users().order_by("last_name", "first_name")

    def exclude_from_search(
        self, existing_queryset: Optional[Union[Collection["User"], QuerySet]] = None  # pylint: disable=unsubscriptable-object
    ) -> Union[Collection["User"], QuerySet]:  # pylint: disable=unsubscriptable-object
        if existing_queryset is None:
            existing_queryset = self

        return existing_queryset.exclude(user_type="service")


class User(AbstractBaseUser, PermissionsMixin):
    """Django User model subclass
    """

    TITLES = (("Mr.", "Mr."), ("Ms.", "Ms."), ("Mrs.", "Mrs."), ("Dr.", "Dr."))

    USER_TYPES = (
        ("student", "Student"),
        ("teacher", "Teacher"),
        ("counselor", "Counselor"),
        ("user", "Attendance-Only User"),
        ("simple_user", "Simple User"),
        ("tjstar_presenter", "tjStar Presenter"),
        ("alum", "Alumnus"),
        ("service", "Service Account"),
    )

    TITLES = (("mr", "Mr."), ("ms", "Ms."), ("mrs", "Mrs."), ("dr", "Dr."))
    # Django Model Fields
    username = models.CharField(max_length=30, unique=True)

    # See Email model for emails
    # See Phone model for phone numbers
    # See Website model for websites

    user_locked = models.BooleanField(default=False)

    # Local internal fields
    first_login = models.DateTimeField(null=True)
    seen_welcome = models.BooleanField(default=False)
    last_global_logout_time = models.DateTimeField(null=True)

    # Local preference fields
    receive_news_emails = models.BooleanField(default=False)
    receive_eighth_emails = models.BooleanField(default=False)

    receive_schedule_notifications = models.BooleanField(default=False)

    student_id = models.CharField(max_length=settings.FCPS_STUDENT_ID_LENGTH, unique=True, null=True)
    user_type = models.CharField(max_length=30, choices=USER_TYPES, default="student")
    admin_comments = models.TextField(blank=True, null=True)
    counselor = models.ForeignKey("self", on_delete=models.SET_NULL, related_name="students", null=True)
    graduation_year = models.IntegerField(null=True)
    title = models.CharField(max_length=5, choices=TITLES, null=True, blank=True)
    first_name = models.CharField(max_length=35, null=True)
    middle_name = models.CharField(max_length=70, null=True)
    last_name = models.CharField(max_length=70, null=True)
    nickname = models.CharField(max_length=35, null=True)
    gender = models.NullBooleanField()
    preferred_photo = models.OneToOneField("Photo", related_name="+", null=True, blank=True, on_delete=models.SET_NULL)
    primary_email = models.OneToOneField("Email", related_name="+", null=True, blank=True, on_delete=models.SET_NULL)
    bus_route = models.ForeignKey(Route, on_delete=models.SET_NULL, null=True)

    # Required to replace the default Django User model
    USERNAME_FIELD = "username"
    """Override default Model Manager (objects) with
    custom UserManager to add table-level functionality."""
    objects = UserManager()

    @staticmethod
    def get_signage_user() -> "User":
        """Returns the user used to authenticate signage displays

        Returns:
            The user used to authenticate signage displays

        """
        return User(id=99999)

    @property
    def address(self) -> Optional["Address"]:
        """Returns the ``Address`` object representing this user's address, or ``None`` if it is not
        set or the current user does not have permission to access it.

        Returns:
            The ``Address`` representing this user's address, or ``None`` if that is unavailable to
            the current user.

        """
        return self.properties.address

    @property
    def schedule(self) -> Optional[Union[QuerySet, Collection["Section"]]]:  # pylint: disable=unsubscriptable-object
        """Returns a QuerySet of the ``Section`` objects representing the classes this student is
        in, or ``None`` if the current user does not have permission to list this student's classes.

        Returns:
            Returns a QuerySet of the ``Section`` objects representing the classes this student is
            in, or ``None`` if the current user does not have permission to list this student's
            classes.

        """
        return self.properties.schedule

    def member_of(self, group: Union[Group, str]) -> bool:
        """Returns whether a user is a member of a certain group.

        Args:
            group: Either the name of a group or a ``Group`` object.

        Returns:
            Whether the user is a member of the given group.

        """
        if isinstance(group, Group):
            group = group.name
        return self.groups.filter(name=group).cache(ops=["exists"], timeout=15).exists()  # pylint: disable=no-member

    def has_admin_permission(self, perm: str) -> bool:
        """Returns whether a user has an admin permission (explicitly, or implied by being in the
        "admin_all" group)

        Args:
            perm: The admin permission to check for.

        Returns:
            Whether the user has the given admin permission (either explicitly or implicitly)

        """
        return self.member_of("admin_all") or self.member_of("admin_" + perm)

    @property
    def full_name(self) -> str:
        """Return full name, e.g. Angela William.

        This is required for subclasses of User.

        Returns:
            The user's full name (first + " " + last).

        """
        return "{} {}".format(self.first_name, self.last_name)

    @property
    def full_name_nick(self) -> str:
        """If the user has a nickname, returns their name in the format "Nickname Lastname."
        Otherwise, this is identical to full_name.

        Returns:
            The user's full name, with their nickname substituted for their first name if it is set.

        """
        return f"{self.nickname or self.first_name} {self.last_name}"

    @property
    def display_name(self) -> str:
        """Returns ``self.full_name``.

        Returns:
            The user's full name.

        """
        return self.full_name

    @property
    def last_first(self) -> str:
        """Return a name in the format of:
            Lastname, Firstname [(Nickname)]
        """
        return "{}, {}".format(self.last_name, self.first_name) + (" ({})".format(self.nickname) if self.nickname else "")

    @property
    def last_first_id(self) -> str:
        """Return a name in the format of:
            Lastname, Firstname [(Nickname)] (Student ID/ID/Username)
        """
        return (
            "{}{} ".format(self.last_name, ", " + self.first_name if self.first_name else "")
            + ("({}) ".format(self.nickname) if self.nickname else "")
            + ("({})".format(self.student_id if self.is_student and self.student_id else self.username))
        )

    @property
    def last_first_initial(self) -> str:
        """Return a name in the format of:
            Lastname, F [(Nickname)]
        """
        return "{}{}".format(self.last_name, ", " + self.first_name[:1] + "." if self.first_name else "") + (
            " ({})".format(self.nickname) if self.nickname else ""
        )

    @property
    def short_name(self) -> str:
        """Return short name (first name) of a user.

        This is required for subclasses of User.

        Returns:
            The user's fist name.

        """
        return self.first_name

    def get_full_name(self) -> str:
        """Return full name, e.g. Angela William.

        Returns:
            The user's full name (see ``full_name``).

        """
        return self.full_name

    def get_short_name(self) -> str:
        """Get short (first) name of a user.

        Returns:
            The user's first name (see ``short_name`` and ``first_name``).

        """
        return self.short_name

    @property
    def primary_email_address(self) -> Optional[str]:
        try:
            return self.primary_email.address if self.primary_email else None
        except Email.DoesNotExist:
            return None

    @property
    def tj_email(self) -> str:
        """Get (or guess) a user's TJ email.

        If a fcps.edu or tjhsst.edu email is specified in their email
        list, use that. Otherwise, append the user's username to the
        proper email suffix, depending on whether they are a student or
        teacher.

        Returns:
            The user's found or guessed FCPS/TJ email address.

        """

        email = self.emails.filter(Q(address__iendswith="@fcps.edu") | Q(address__iendswith="@tjhsst.edu")).first()
        if email is not None:
            return email.address

        if self.is_teacher:
            domain = "fcps.edu"
        else:
            domain = "tjhsst.edu"

        return "{}@{}".format(self.username, domain)

    @property
    def non_tj_email(self) -> Optional[str]:
        """
        Returns the user's first non-TJ email found, or None if none is found.

        If a user has a primary email set and it is not their TJ email,
        use that. Otherwise, use the first email found that is not their
        TJ email.

        Returns:
            The first non-TJ email found for a user, or None if no such email is found.

        """
        tj_email = self.tj_email
        primary_email_address = self.primary_email_address

        if primary_email_address and primary_email_address.lower() != tj_email.lower():
            return primary_email_address

        email = self.emails.exclude(address__iexact=tj_email).first()
        return email.address if email else None

    @property
    def notification_email(self) -> str:
        """Returns the notification email.

        If a primary email is set, use it. Otherwise, use the first
        email on file. If no email addresses exist, use the user's
        TJ email.

        Returns:
            A user's notification email address.

        """

        primary_email_address = self.primary_email_address
        if primary_email_address:
            return primary_email_address

        email = self.emails.first()
        return email.address if email and email.address else self.tj_email

    @property
    def default_photo(self) -> Optional[bytes]:
        """Returns default photo (in binary) that should be used

        Returns:
            The binary representation of the user's default photo.

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

        return None

    @property
    def grade(self) -> "Grade":
        """Returns the grade of a user.

        Returns:
            A Grade object representing the uset's current grade.

        """
        return Grade(self.graduation_year)

    @property
    def permissions(self) -> Dict[str, bool]:
        """Dynamically generate dictionary of privacy options.

        Returns:
            A dictionary mapping the name of each privacy option to a boolean indicating whether it
            is enabled.

        """
        permissions_dict = {}

        for prefix in PERMISSIONS_NAMES:
            permissions_dict[prefix] = {}
            for suffix in PERMISSIONS_NAMES[prefix]:
                permissions_dict[prefix][suffix] = getattr(self.properties, prefix + "_" + suffix)

        return permissions_dict

    def _current_user_override(self) -> bool:
        """Return whether the currently logged in user is a teacher or eighth admin, and can view
        all of a student's information regardless of their privacy settings.

        Returns:
            Whether the user has permissions to view all of their information regardless of their
            privacy settings.

        """
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
            logger.error("Could not check teacher/eighth override: %s", e)
            can_view_anyway = False
        return can_view_anyway

    @property
    def ion_username(self) -> str:
        """Returns this user's username.

        Returns:
            This user's username (see ``username``).

        """
        return self.username

    @property
    def grade_number(self) -> int:
        """Returns the number of the grade this user is currently in (9, 10, 11, or 12 for
        students).

        Returns:
            The number of the grade this user is currently in.

        """
        return self.grade.number

    @property
    def sex(self) -> str:
        """Returns "Male" if this user is male, "Female" otherwise.

        Returns:
            "Male" if this user is male, "Female" otherwise.

        """
        return "Male" if self.is_male else "Female"

    @property
    def is_male(self) -> bool:
        """Returns whether the user is male.

        Returns:
            Whether the user is male.

        """
        return self.gender is True

    @property
    def is_female(self) -> bool:
        """Returns whether the user is female.

        Returns:
            Whether the user is female.

        """
        return self.gender is False

    @property
    def can_view_eighth(self) -> bool:
        """Checks if a user has the show_eighth permission.

        Returns:
            Whether this user has made their eighth period signups public.

        """

        return self.properties.attribute_is_visible("show_eighth")

    @property
    def can_view_phone(self) -> bool:
        """Checks if a user has the show_telephone permission.

        Returns:
            Whether this user has made their phone number public.

        """

        return self.properties.attribute_is_visible("show_telephone")

    @property
    def is_eighth_admin(self) -> bool:
        """Checks if user is an eighth period admin.

        Returns:
            Whether this user is an eighth period admin.

        """

        return self.has_admin_permission("eighth")

    @property
    def has_print_permission(self) -> bool:
        """Checks if user has the admin permission 'printing'.

        Returns:
            Whether this user is a printing administrator.

        """

        return self.has_admin_permission("printing")

    @property
    def is_parking_admin(self) -> bool:
        """Checks if user has the admin permission 'parking'.

        Returns:
            Whether this user is a parking administrator.

        """

        return self.has_admin_permission("parking")

    @property
    def is_bus_admin(self) -> bool:
        """Returns whether the user has the ``bus`` admin permission.

        Returns:
            Whether the user has the ``bus`` admin permission.

        """
        return self.has_admin_permission("bus")

    @property
    def can_request_parking(self) -> bool:
        """Checks if user can view the parking interface.

        Returns:
            Whether this user can view the parking interface and request a parking spot.

        """
        return self.grade_number >= 11 or self.is_parking_admin

    @property
    def is_announcements_admin(self) -> bool:
        """Checks if user is an announcements admin.

        Returns:
            Whether this user is an announcement admin.

        """

        return self.has_admin_permission("announcements")

    @property
    def is_schedule_admin(self) -> bool:
        """Checks if user is a schedule admin.

        Returns:
            Whether this user is a schedule admin.

        """

        return self.has_admin_permission("schedule")

    @property
    def is_board_admin(self) -> bool:
        """Checks if user is a board admin.

        Returns:
            Whether this user is a board admin.

        """

        return self.has_admin_permission("board")

    def can_manage_group(self, group: Union[Group, str]) -> bool:
        """Checks whether this user has permission to edit/manage the given group (either
        a Group or a group name).

        WARNING: Granting permission to edit/manage "admin_" groups gives that user control
        over nearly all data on Ion!

        Args:
            group: The group to check permissions for.

        Returns:
            Whether this user has permission to edit/manage the given group.

        """

        if isinstance(group, Group):
            group = group.name

        if group.startswith("admin_"):
            return self.is_superuser

        return self.is_eighth_admin

    @property
    def is_teacher(self) -> bool:
        """Checks if user is a teacher.

        Returns:
            Whether this user is a teacher.

        """
        return self.user_type == "teacher" or self.user_type == "counselor"

    @property
    def is_student(self) -> bool:
        """Checks if user is a student.

        Returns:
            Whether this user is a student.

        """
        return self.user_type == "student"

    @property
    def is_alum(self) -> bool:
        """Checks if user is an alumnus.

        Returns:
            Whether this user is an alumnus.

        """
        return self.user_type == "alum"

    @property
    def is_senior(self) -> bool:
        """Checks if user is a student in Grade 12.

        Returns:
            Whether this user is a senior.

        """
        return self.is_student and self.grade_number == 12

    @property
    def is_eighthoffice(self) -> bool:
        """Checks if user is an Eighth Period office user.

        This is currently hardcoded, but is meant to be used instead
        of user.id == 9999 or user.username == "eighthoffice".

        Returns:
            Whether this user is an Eighth Period office user.

        """
        return self.id == 9999

    @property
    def is_active(self) -> bool:
        """Checks if the user is active.

        This is currently used to catch invalid logins.

        Returns:
            Whether the user is "active" -- i.e. their account is not locked.

        """

        return not self.username.startswith("INVALID_USER") and not self.user_locked

    @property
    def is_restricted(self) -> bool:
        """Checks if user needs the restricted view of Ion

        This applies to users that are user_type 'user', user_type 'alum'
        or user_type 'service'

        Returns:
            Whether this user should see a restricted view of Ion.

        """

        return self.user_type in ["user", "alum", "service"]

    @property
    def is_staff(self) -> bool:
        """Checks if a user should have access to the Django Admin interface.

        This has nothing to do with staff at TJ - `is_staff`
        has to be overridden to make this a valid user model.

        Returns:
            Whether the user should have access to the Django Admin interface.

        """

        return self.is_superuser or self.has_admin_permission("staff")

    @property
    def is_attendance_user(self) -> bool:
        """Checks if user is an attendance-only user.

        Returns:
            Whether this user is an attendance-only user.

        """
        return self.user_type == "user"

    @property
    def is_simple_user(self) -> bool:
        """Checks if user is a simple user (e.g. eighth office user)

        Returns:
            Whether this user is a simple user (e.g. eighth office user).

        """
        return self.user_type == "simple_user"

    @property
    def has_senior(self) -> bool:
        """Checks if a ``Senior`` model (see ``intranet.apps.seniors.models.Senior`` exists for the
        current user.

        Returns:
            Whether a ``Senior`` model (see ``intranet.apps.seniors.models.Senior`` exists for the
            current user.

        """
        try:
            self.senior
        except AttributeError:
            return False
        return True

    @property
    def is_attendance_taker(self) -> bool:
        """Checks if this user can take attendance for an eighth activity.

        Returns:
            Whether this  user can take attendance for an eighth activity.

        """
        return self.is_eighth_admin or self.is_teacher or self.is_attendance_user

    @property
    def is_eighth_sponsor(self) -> bool:
        """Determine whether the given user is associated with an.

        :class:`intranet.apps.eighth.models.EighthSponsor` and, therefore, should view activity
        sponsoring information.

        Returns:
            Whether this user is an eighth period sponsor.

        """
        return EighthSponsor.objects.filter(user=self).exists()

    @property
    def frequent_signups(self):
        """Return a QuerySet of activity id's and counts for the activities that a given user
        has signed up for more than `settings.SIMILAR_THRESHOLD` times"""
        key = "{}:frequent_signups".format(self.username)
        cached = cache.get(key)
        if cached:
            return cached
        freq_signups = (
            self.eighthsignup_set.exclude(scheduled_activity__activity__administrative=True)
            .exclude(scheduled_activity__activity__special=True)
            .exclude(scheduled_activity__activity__restricted=True)
            .exclude(scheduled_activity__activity__deleted=True)
            .values("scheduled_activity__activity")
            .annotate(count=Count("scheduled_activity__activity"))
            .filter(count__gte=settings.SIMILAR_THRESHOLD)
            .order_by("-count")
        )
        cache.set(key, freq_signups, timeout=60 * 60 * 24 * 7)
        return freq_signups

    @property
    def recommended_activities(self):
        key = "{}:recommended_activities".format(self.username)
        cached = cache.get(key)
        if cached is not None:
            return cached
        acts = set()
        for signup in (
            self.eighthsignup_set.exclude(scheduled_activity__activity__administrative=True)
            .exclude(scheduled_activity__activity__special=True)
            .exclude(scheduled_activity__activity__restricted=True)
            .exclude(scheduled_activity__activity__deleted=True)
            .exclude(scheduled_activity__block__date__lte=(timezone.localtime() + relativedelta(months=-6)))
        ):
            acts.add(signup.scheduled_activity.activity)
        close_acts = set()
        for act in acts:
            sim = act.similarities.order_by("-weighted").first()
            if sim and sim.weighted > 1:
                close_acts.add(sim.activity_set.exclude(id=act.id).first())
        cache.set(key, close_acts, timeout=60 * 60 * 24 * 7)
        return close_acts

    def archive_admin_comments(self):
        current_year = timezone.localdate().year
        previous_year = current_year - 1
        self.admin_comments = "\n=== {}-{} comments ===\n{}".format(previous_year, current_year, self.admin_comments)
        self.save(update_fields=["admin_comments"])

    def get_eighth_sponsor(self):
        """Return the ``EighthSponsor`` that this user is associated with.

        Returns:
            The ``EighthSponsor`` that this user is associated with.

        """
        try:
            sp = EighthSponsor.objects.get(user=self)
        except EighthSponsor.DoesNotExist:
            return False

        return sp

    def has_unvoted_polls(self) -> bool:
        """Returns whether there are open polls thet this user has not yet voted in.

        Returns:
            Whether there are open polls thet this user has not yet voted in.

        """
        now = timezone.localtime()
        return Poll.objects.visible_to_user(self).filter(start_time__lt=now, end_time__gt=now).exclude(question__answer__user=self).exists()

    def signed_up_today(self) -> bool:
        """If the user is a student, returns whether they are signed up for an activity during
        all eighth period blocks that are scheduled today. Otherwise, returns ``True``.

        Returns:
            If the user is a student, returns whether they are signed up for an activity during
            all eighth period blocks that are scheduled today. Otherwise, returns ``True``.

        """
        if not self.is_student:
            return True

        return not EighthBlock.objects.get_blocks_today().exclude(eighthscheduledactivity__eighthsignup_set__user=self).exists()

    def signed_up_next_few_days(self, *, num_days: int = 3) -> bool:
        """If the user is a student, returns whether they are signed up for an activity during
        all eighth period blocks in the next ``num_days`` days. Otherwise, returns ``True``.

        Today is counted as a day, so ``signed_up_few_next_day(num_days=1)`` is equivalent to
        ``signed_up_today()``.

        Args:
            num_days: The number of days (including today) on which to search for blocks during
                which the user is signed up.

        Returns:
            If the user is a student, returns whether they are signed up for an activity during
            all eighth period blocks in the next ``num_days`` days. Otherwise, returns ``True``.

        """
        if not self.is_student:
            return True

        today = timezone.localdate()
        end_date = today + timedelta(days=num_days - 1)

        return (
            not EighthBlock.objects.filter(date__gte=today, date__lte=end_date).exclude(eighthscheduledactivity__eighthsignup_set__user=self).exists()
        )

    def absence_count(self) -> int:
        """Return the user's absence count.

        If the user has no absences or is not a signup user, returns 0.

        Returns:
            The number of absences this user has.

        """
        return EighthSignup.objects.filter(user=self, was_absent=True, scheduled_activity__attendance_taken=True).count()

    def absence_info(self):
        """Returns a ``QuerySet`` of the ``EighthSignup``s for which this user was absent.

        Returns:
            A ``QuerySet`` of the ``EighthSignup``s for which this user was absent.

        """
        return EighthSignup.objects.filter(user=self, was_absent=True, scheduled_activity__attendance_taken=True)

    def handle_delete(self):
        """Handle a graduated user being deleted."""
        from intranet.apps.eighth.models import EighthScheduledActivity  # pylint: disable=import-outside-toplevel

        EighthScheduledActivity.objects.filter(eighthsignup_set__user=self).update(archived_member_count=F("archived_member_count") + 1)

    def __getattr__(self, name):
        if name == "properties":
            return UserProperties.objects.get_or_create(user=self)[0]
        elif name == "dark_mode_properties":
            return UserDarkModeProperties.objects.get_or_create(user=self)[0]
        raise AttributeError("{!r} object has no attribute {!r}".format(type(self).__name__, name))

    def __str__(self):
        return self.username or self.ion_username or str(self.id)

    def __int__(self):
        return self.id


class UserProperties(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="properties", on_delete=models.CASCADE)

    _address = models.OneToOneField("Address", null=True, blank=True, on_delete=models.SET_NULL)
    _schedule = models.ManyToManyField("Section", related_name="_students")
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

    self_show_eighth = models.BooleanField(default=False)
    parent_show_eighth = models.BooleanField(default=False)

    self_show_schedule = models.BooleanField(default=False)
    parent_show_schedule = models.BooleanField(default=False)

    def __getattr__(self, name):
        if name.startswith("self") or name.startswith("parent"):
            return object.__getattribute__(self, name)
        if name == "address":
            return self._address if self.attribute_is_visible("show_address") else None
        if name == "schedule":
            return self._schedule if self.attribute_is_visible("show_schedule") else None
        raise AttributeError("{!r} object has no attribute {!r}".format(type(self).__name__, name))

    def __setattr__(self, name, value):
        if name == "address":
            if self.attribute_is_visible("show_address"):
                self._address = value
        super(UserProperties, self).__setattr__(name, value)  # pylint: disable=no-member; Pylint is wrong

    def __str__(self):
        return self.user.__str__()

    def set_permission(self, permission: str, value: bool, parent: bool = False, admin: bool = False) -> bool:
        """Sets permission for personal information.

        Returns False silently if unable to set permission. Returns True if successful.

        Args:
            permission: The name of the permission to set.
            value: The value to set the permission to.
            parent: Whether to set the parent's permission instead of the student's permission. If
                ``parent`` is ``True`` and ``value`` is ``False``, both the parent and the student's
                permissions will be set to ``False``.
            admin: If set to ``True``, this will allow changing the student's permission even if the
                parent's permission is set to ``False`` (normally, this causes an error).

        """
        try:
            if not getattr(self, "parent_{}".format(permission)) and not parent and not admin:
                return False
            level = "parent" if parent else "self"
            setattr(self, "{}_{}".format(level, permission), value)

            update_fields = ["{}_{}".format(level, permission)]

            # Set student permission to false if parent sets permission to false.
            if parent and not value:
                setattr(self, "self_{}".format(permission), False)
                update_fields.append("self_{}".format(permission))

            self.save(update_fields=update_fields)
            return True
        except Exception as e:
            logger.error("Error occurred setting permission %s to %s: %s", permission, value, e)
            return False

    def _current_user_override(self) -> bool:
        """Return whether the currently logged in user is a teacher, and can view all of a student's
        information regardless of their privacy settings.

        Returns:
            Whether the currently logged in user can view all of a student's information regardless
            of their privacy settings.

        """
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
            logger.error("Could not check teacher/eighth override: %s", e)
            can_view_anyway = False
        return can_view_anyway

    def is_http_request_sender(self) -> bool:
        """Checks if a user the HTTP request sender (accessing own info)

        Used primarily to load private personal information from the
        cache. (A student should see all info on his or her own profile
        regardless of how the permissions are set.)

        Returns:
            Whether the user is the sender of the current HTTP request.

        """
        try:
            # threadlocals is a module, not an actual thread locals object
            request = threadlocals.request()
            if request and request.user and request.user.is_authenticated:
                requesting_user_id = request.user.id
                return str(requesting_user_id) == str(self.user.id)
        except (AttributeError, KeyError) as e:
            logger.error("Could not check request sender: %s", e)
            return False

        return False

    def attribute_is_visible(self, permission: str) -> bool:
        """Checks privacy options to see if an attribute is visible to the user sending the current
        HTTP request.

        Args:
            permission: The name of the permission to check.

        Returns:
            Whether the user sending the current HTTP request has permission to view the given
            permission.

        """
        try:
            parent = getattr(self, "parent_{}".format(permission))
            student = getattr(self, "self_{}".format(permission))
            return (parent and student) or (self.is_http_request_sender() or self._current_user_override())
        except Exception:
            logger.error("Could not retrieve permissions for %s", permission)

    def attribute_is_public(self, permission: str) -> bool:
        """Checks if attribute is visible to public (ignoring whether the user sending the HTTP
        request has permission to access it).

        Args:
            permission: The name of the permission to check.

        Returns:
            Whether the given permission is public.

        """
        try:
            parent = getattr(self, "parent_{}".format(permission))
            student = getattr(self, "self_{}".format(permission))
            return parent and student
        except Exception:
            logger.error("Could not retrieve permissions for %s", permission)


PERMISSIONS_NAMES = {
    prefix: [name[len(prefix) + 1:] for name in dir(UserProperties) if name.startswith(prefix + "_")] for prefix in ["self", "parent"]
}


class UserDarkModeProperties(models.Model):
    """
    Contains user properties relating to dark mode
    """

    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="dark_mode_properties", on_delete=models.CASCADE)
    dark_mode_enabled = models.BooleanField(default=False)

    def __str__(self):
        return str(self.user)


class Email(models.Model):
    """Represents an email address"""

    address = models.EmailField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="emails", on_delete=models.CASCADE)

    def __str__(self):
        return self.address

    class Meta:
        unique_together = ("user", "address")


class Phone(models.Model):
    """Represents a phone number"""

    PURPOSES = (("h", "Home Phone"), ("m", "Mobile Phone"), ("o", "Other Phone"))

    purpose = models.CharField(max_length=1, choices=PURPOSES, default="o")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="phones", on_delete=models.CASCADE)
    _number = PhoneField()  # validators should be a list

    def __setattr__(self, name, value):
        if name == "number":
            if self.user.properties.attribute_is_visible("show_telephone"):
                self._number = value
                self.save(update_fields=["_number"])
        else:
            super(Phone, self).__setattr__(name, value)  # pylint: disable=no-member; Pylint is wrong

    def __getattr__(self, name):
        if name == "number":
            return self._number if self.user.properties.attribute_is_visible("show_telephone") else None
        raise AttributeError("{!r} object has no attribute {!r}".format(type(self).__name__, name))

    def __str__(self):
        return "{}: {}".format(self.get_purpose_display(), self.number)

    class Meta:
        unique_together = ("user", "_number")


class Website(models.Model):
    """Represents a user's website"""

    url = models.URLField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="websites", on_delete=models.CASCADE)

    def __str__(self):
        return self.url

    class Meta:
        unique_together = ("user", "url")


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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="photos", on_delete=models.CASCADE)

    def __setattr__(self, name, value):
        if name == "binary":
            if self.user.properties.attribute_is_visible("show_pictures"):
                self._binary = value
                self.save(update_fields=["_binary"])
        else:
            super(Photo, self).__setattr__(name, value)  # pylint: disable=no-member; Pylint is wrong

    def __getattr__(self, name):
        if name == "binary":
            return self._binary if self.user.properties.attribute_is_visible("show_pictures") else None
        raise AttributeError("{!r} object has no attribute {!r}".format(type(self).__name__, name))

    @cached_property
    def base64(self) -> Optional[bytes]:
        """Returns base64 encoded binary data for a user's picture.

        Returns:
           Base 64-encoded binary data for a user's picture.

        """

        binary = self.binary
        if binary:
            return b64encode(binary)
        return None


class Grade:
    """Represents a user's grade."""

    names = [elem[1] for elem in GRADE_NUMBERS]

    def __init__(self, graduation_year):
        """Initialize the Grade object.

        Args:
            graduation_year
                The numerical graduation year of the user

        """
        if graduation_year is None:
            self._number = 13
        else:
            self._number = get_senior_graduation_year() - int(graduation_year) + 12

        if 9 <= self._number <= 12:
            self._name = [elem[1] for elem in GRADE_NUMBERS if elem[0] == self._number][0]
        else:
            self._name = "graduate"

    @property
    def number(self) -> int:
        """Return the grade as a number (9-12).

        For use in templates since there is no nice integer casting.
        In Python code you can also use int() on a Grade object.

        """
        return self._number

    @property
    def name(self) -> str:
        """Return the grade's name (e.g. senior)"""
        return self._name

    @property
    def name_plural(self) -> str:
        """Return the grade's plural name (e.g. freshmen)"""
        return "freshmen" if (self._number and self._number == 9) else "{}s".format(self._name) if self._name else ""

    @property
    def text(self) -> str:
        """Return the grade's number as a string (e.g. Grade 12, Graduate)"""
        if 9 <= self._number <= 12:
            return "Grade {}".format(self._number)
        else:
            return self._name

    @staticmethod
    def number_from_name(name: str) -> Optional[int]:
        if name in Grade.names:
            return Grade.names.index(name) + 9
        return None

    @classmethod
    def grade_from_year(cls, graduation_year: int) -> int:
        today = timezone.localdate()
        if today.month >= settings.YEAR_TURNOVER_MONTH:
            current_senior_year = today.year + 1
        else:
            current_senior_year = today.year

        return current_senior_year - graduation_year + 12

    @classmethod
    def year_from_grade(cls, grade: int) -> int:
        today = timezone.localdate()
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

    class Meta:
        ordering = ("name", "course_id")


class Section(models.Model):
    """Represents a section - a class with teacher, period, and room assignments"""

    course = models.ForeignKey(Course, related_name="sections", on_delete=models.CASCADE)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    room = models.CharField(max_length=16)
    period = models.IntegerField()
    section_id = models.CharField(max_length=16, unique=True)
    sem = models.CharField(max_length=2)

    def __str__(self):
        return "{} ({}) - {} Pd. {}".format(self.course.name, self.section_id, self.teacher.full_name if self.teacher else "Unknown", self.period)

    def __getattr__(self, name):
        if name == "students":
            return [s.user for s in self._students.all() if s.attribute_is_visible("show_schedule")]
        raise AttributeError("{!r} object has no attribute {!r}".format(type(self).__name__, name))

    class Meta:
        ordering = ("section_id", "period")
