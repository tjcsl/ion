# -*- coding: utf-8 -*-

import hashlib
import logging
import os
from base64 import b64encode
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager as DjangoUserManager
from django.core import exceptions
from django.core.cache import cache
from django.core.signing import Signer
from django.db import models

from intranet.db.ldap_db import LDAPConnection, LDAPFilter
from intranet.middleware import threadlocals

import ldap3
import ldap3.utils.dn

from ..groups.models import Group

logger = logging.getLogger(__name__)


class UserManager(DjangoUserManager):
    """User model Manager for table-level User queries.

    Provides table-level LDAP abstraction for the User model. If a call
    to a method fails for this Manager, the call is deferred to the
    default User model manager.

    """

    def user_with_student_id(self, student_id):
        """Get a unique user object by student ID."""
        c = LDAPConnection()

        results = c.search(settings.USER_DN, "tjhsstStudentId={}".format(student_id), ["dn"])

        if len(results) == 1:
            return User.get_user(dn=results[0]["dn"])
        return None

    def user_with_ion_id(self, student_id):
        """Get a unique user object by Ion ID."""
        c = LDAPConnection()

        results = c.search(settings.USER_DN, "iodineUidNumber={}".format(student_id), ["dn"])

        if len(results) == 1:
            return User.get_user(dn=results[0]["dn"])
        return None

    def users_in_year(self, year):
        """Get a list of users in a specific graduation year."""
        c = LDAPConnection()

        results = c.search(settings.USER_DN, "graduationYear={}".format(year), ["dn"])

        users = []
        for user in results:
            users.append(User.get_user(dn=user["dn"]))

        return users

    def _ldap_and_string(self, opts):
        """Combine LDAP queries with AND.

        e.x.: ["a=b"]        => "a=b"
              ["a=b", "c=d"] => "(&(a=b)(c=d))"

        """
        if len(opts) == 1:
            return opts[0]
        else:
            return "(&" + "".join(["({})".format(i) for i in opts]) + ")"

    def user_with_name(self, given_name=None, sn=None):
        """Get a unique user object by given name (first/nickname and last)."""
        c = LDAPConnection()

        results = []

        if sn and not given_name:
            results = c.search(settings.USER_DN, "sn={}".format(sn), ["dn"])
        elif given_name:
            query = ["givenName={}".format(given_name)]
            if sn:
                query.append("sn={}".format(sn))
            results = c.search(settings.USER_DN, self._ldap_and_string(query), ["dn"])

            if len(results) == 0:
                # Try their first name as a nickname
                query[0] = "nickname={}".format(given_name)
                results = c.search(settings.USER_DN, self._ldap_and_string(query), ["dn"])

        if len(results) == 1:
            return User.get_user(dn=results[0]["dn"])

        return None

    def users_with_birthday(self, month, day):
        """Return a list of user objects who have a birthday on a given date."""
        c = LDAPConnection()

        month = int(month)
        if month < 10:
            month = "0" + str(month)

        day = int(day)
        if day < 10:
            day = "0" + str(day)

        search_query = "birthday=*{}{}".format(month, day)
        results = c.search(settings.USER_DN, search_query, ["dn"])

        users = []
        for res in results:
            u = User.get_user(dn=res["dn"])
            if u.attribute_is_visible("showbirthday"):
                users.append(u)

        return users

    # Simple way to filter out teachers and students without hitting LDAP.
    # This shouldn't be a problem unless the username scheme changes and
    # the consequences of error are not significant.

    # FIXME: save userClass in db.

    def get_students(self):
        """Get user objects that are students (quickly)."""
        key = "users:students"
        cached = cache.get(key)
        if cached:
            logger.debug("Using cached User.get_students")
            return cached
        else:
            try:
                users = Group.objects.get(name__istartswith="All Students").user_set.all()
            except Group.DoesNotExist:
                users = User.objects.filter(username__startswith="2")
            # Add possible exceptions handling here
            logger.debug("Set cache for User.get_students")
            cache.set(key, users, timeout=settings.CACHE_AGE['users_list'])
            return users

    def get_teachers(self):
        """Get user objects that are teachers (quickly)."""
        key = "users:teachers"
        cached = cache.get(key)
        if cached:
            logger.debug("Using cached User.get_teachers")
            return cached
        else:
            users = User.objects.exclude(username__startswith="2")
            # Add possible exceptions handling here
            users = users | User.objects.filter(id=31863)
            logger.debug("Set cache for User.get_teachers")
            cache.set(key, users, timeout=settings.CACHE_AGE['users_list'])
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
        teachers.sort(key=lambda u: (u[0], u[1]))
        for t in teachers:
            if t[0] is None or len(t[0]) <= 1 or t[2] in [8888, 7011]:
                teachers.remove(t)
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

    # Django Model Fields
    username = models.CharField(max_length=30, unique=True)

    # Local internal fields
    first_login = models.DateTimeField(null=True)
    seen_welcome = models.BooleanField(default=False)

    # Local preference fields
    receive_news_emails = models.BooleanField(default=False)
    receive_eighth_emails = models.BooleanField(default=False)

    receive_schedule_notifications = models.BooleanField(default=False)

    # Private dn cache
    _dn = None  # type: str

    # Required to replace the default Django User model
    USERNAME_FIELD = "username"
    """Override default Model Manager (objects) with
    custom UserManager to add table-level functionality."""
    objects = UserManager()

    @classmethod
    def get_user(cls, dn=None, id=None, username=None):
        """Retrieve a user object from LDAP and save it to the SQL database if necessary.

        Creates a User object from a dn, user id, or a username based on
        data in the LDAP database. If the user also exists in the SQL
        database, it is linked up with that model. If it does not exist,
        then it is created.

        Args:
            dn
                The full LDAP Distinguished Name of a user.
            id
                The user ID of the user to return.
            username
                The username of the user to return.

        Returns:
            The User object if the user could be found in LDAP,
            otherwise User.DoesNotExist is raised.

        """

        if id is not None:
            try:
                user = User.objects.get(id=id)
            except User.DoesNotExist:
                user_dn = User.dn_from_id(id)
                if user_dn is not None:
                    user = User.get_user(dn=user_dn)
                else:
                    raise User.DoesNotExist("`User` with ID {} does not exist.".format(id))

        elif username is not None:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                user_dn = User.dn_from_username(username)
                user = User.get_user(dn=user_dn)
        elif dn is not None:
            try:
                user = User(dn=dn)
                user.id = user.ion_id

                try:
                    user = User.objects.get(id=user.id)
                except User.DoesNotExist:
                    if user.ion_username and user.ion_id:
                        user.username = user.ion_username

                        user.set_unusable_password()
                        user.last_login = datetime(9999, 1, 1)

                        user.save()
                    else:
                        raise User.DoesNotExist("`User` with DN '{}' does not have a username.".format(dn))
            except (ldap3.LDAPInvalidDNSyntaxResult, ldap3.LDAPNoSuchObjectResult):
                raise User.DoesNotExist("`User` with DN '{}' does not exist.".format(dn))
        else:
            raise TypeError("get_user() requires at least one argument.")

        return user

    @staticmethod
    def dn_from_id(id):
        """Get a dn, given an ID.

        Args:
            id
                the ID of the user.

        Returns:
            String if dn was found, otherwise None

        """
        logger.debug("Fetching DN of User with ID {}.".format(id))
        key = ":".join([str(id), 'dn'])
        cached = cache.get(key)

        if cached:
            logger.debug("DN of User with ID {} loaded " "from cache.".format(id))
            return cached
        else:
            c = LDAPConnection()
            result = c.search(settings.USER_DN, "iodineUidNumber={}".format(id), ['dn'])
            if len(result) == 1:
                dn = result[0]['dn']
            else:
                logger.debug("No such User with ID {}.".format(id))
                dn = None
            cache.set(key, dn, timeout=settings.CACHE_AGE['dn_id_mapping'])
            return dn

    @staticmethod
    def dn_from_username(username):
        # logger.debug("Fetching DN of User with username {}.".format(username))
        return "iodineUid=" + ldap3.utils.dn.escape_attribute_value(username) + "," + settings.USER_DN

    @staticmethod
    def username_from_dn(dn):
        # logger.debug("Fetching username of User with ID {}.".format(id))
        return ldap3.utils.dn.parse_dn(dn)[0][1]

    @staticmethod
    def create_secure_cache_key(identifier):
        """Create a cache key for sensitive information.

        Caching personal information that was once access-protected
        introduces an inherent security risk. To prevent human retrieval
        of a value from the cache, the plaintext key is first signed
        with the secret key and then hashed using the SHA1 algorithm.
        That way, one would need the secret key to query for a specific
        cached value and an existing key would indicate nothing about
        the relevance of the cooresponding value. For maximum
        effectiveness, cache attributes of an object separately so the
        context of a cached value can not be inferred (e.g. cache a
        user's name separate from his or her address so the two can not
        be associated).

        This effectively makes sure non-root users on the production
        server can't access private data from the cache.

        Args:
            identifier
                The plaintext identifier (generally of the form
                "<dn>.<attribute>" for the cached data).

        Returns:
            String

        """

        if os.environ.get("SECURE_CACHE", "YES") == "NO":
            return identifier
        signer = Signer()
        signed = signer.sign(identifier)
        hash = hashlib.sha1(signed.encode())
        return hash.hexdigest()

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
        if not hasattr(self, "_groups_cache"):
            self._groups_cache = self.groups.values_list("name", flat=True)

        if isinstance(group, Group):
            group = group.name

        return group in self._groups_cache

    def has_admin_permission(self, perm):
        """Returns whether a user has an admin permission (explicitly, or implied by being in the
        "admin_all" group)

        Returns:
            Boolean

        """

        if perm == "ldap":
            # not all of admin_all has LDAP permissions
            return self.member_of("admin_ldap")

        return self.member_of("admin_all") or self.member_of("admin_" + perm)

    @property
    def full_name(self):
        """Return full name, e.g. Angela William.

        This is required for subclasses of User.

        """
        return self.common_name

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
        return ("{}, {} ".format(self.last_name, self.first_name) + ("({})".format(self.nickname) if self.nickname else ""))

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
    def dn(self):
        """Return the full distinguished name for a user in LDAP."""
        if not self._dn and self.id:
            self._dn = User.dn_from_id(self.id)
        elif self.username:
            self._dn = User.dn_from_username(self.username)
        return self._dn

    @dn.setter
    def dn(self, dn):
        """Set DN for a user."""
        if not self._dn:
            self._dn = dn
        # if not self.username:
        # self.username = ldap.dn.str2dn(dn)[0][0][1]

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

    @property
    def grade(self):
        """Returns the grade of a user.

        Returns:
            Grade object

        """
        if not self.dn:
            return None
        key = ":".join([self.dn, 'grade'])

        cached = cache.get(key)

        if cached:
            logger.debug("Grade of user {} loaded from cache.".format(self.id))
            return cached
        else:
            grade = Grade(self.graduation_year)

            cache.set(key, grade, timeout=settings.CACHE_AGE['ldap_permissions'])
            return grade

    def _current_user_override(self):
        """Return whether the currently logged in user is a teacher, and can view all of a student's
        information regardless of their privacy settings."""
        try:
            # threadlocals is a module, not an actual thread locals object
            requesting_user = threadlocals.request().user
            can_view_anyway = (requesting_user.is_teacher or requesting_user.is_eighthoffice)
        except (AttributeError, KeyError):
            can_view_anyway = False

        return can_view_anyway

    @property
    def classes(self):
        """Returns a list of Class objects for a user ordered by period number.

        Returns:
            List of Class objects

        """
        is_student = self.is_student

        identifier = ":".join([self.dn, "classes"])
        key = User.create_secure_cache_key(identifier)

        cached = cache.get(key)
        if self.is_http_request_sender():
            visible = True
        elif self._current_user_override():
            visible = True
        elif is_student:
            visible = self.attribute_is_visible("showschedule")
        else:
            visible = True

        if cached and visible:
            logger.debug("Attribute 'classes' of user {} loaded from cache.".format(self.id))
            schedule = []
            for dn in cached:
                class_object = Class(dn=dn)
                schedule.append(class_object)

            return schedule
        elif not cached and visible:
            c = LDAPConnection()
            try:
                if is_student:
                    results = c.user_attributes(self.dn, ['enrolledclass'])
                    classes = results.first_result()["enrolledclass"]
                else:
                    query = LDAPFilter.and_filter("objectClass=tjhsstClass", "sponsorDn=" + self.dn)
                    results = c.search(settings.CLASS_DN, query, ["dn"])
                    classes = [r["dn"] for r in results]

                logger.debug("Classes: {}".format(classes))
            except KeyError:
                return None
            else:
                schedule = []
                for dn in classes:
                    class_object = Class(dn=dn)

                    # Temporarily pack the classes in tuples so we can
                    # sort on an integer key instead of the periods
                    # property to avoid tons of needless LDAP queries
                    #
                    sortvalue = class_object.sortvalue
                    schedule.append((sortvalue, class_object, dn))

                ordered_schedule = sorted(schedule, key=lambda e: e[0])
                if not ordered_schedule:
                    return None
                # Prepare a list of DNs for caching
                # (pickling a Class class loads all properties
                # recursively and quickly reaches the maximum
                # recursion depth)
                dn_list = list(zip(*ordered_schedule))[2]
                cache.set(key, dn_list, timeout=settings.CACHE_AGE['user_classes'])
                return list(zip(*ordered_schedule))[1]  # Unpacked class list
        else:
            return None

    @property
    def ionldap_courses(self):
        if self.is_student:
            courses = self.ldapcourse_set.all()
        elif self.is_teacher:
            # FIXME: refactor to remove recursive dep
            from ..ionldap.models import LDAPCourse
            courses = LDAPCourse.objects.filter(teacher_name="{}, {}".format(self.last_name, self.first_name))
        else:
            return None

        return courses.order_by("period", "end_period")

    @property
    def counselor(self):
        """Returns a user's counselor as a User object.

        Returns:
            :class:`User` object for the user's counselor

        """
        key = ":".join([self.dn, "counselor"])

        cached = cache.get(key)

        if cached:
            logger.debug("Attribute 'counselor' of user {} loaded " "from cache.".format(self.id))
            user_object = User.get_user(id=cached)
            return user_object
        else:
            c = LDAPConnection()
            try:
                result = c.user_attributes(self.dn, ["counselor"])
                counselor = result.first_result()["counselor"][0]
            except KeyError:
                return None
            else:
                cache.set(key, counselor, timeout=settings.CACHE_AGE['user_attribute'])
                user_object = User.get_user(id=counselor)
                return user_object

    @property
    def address(self):
        """Returns the address of a user.

        Returns:
            Address object

        """
        identifier = ":".join([self.dn, "address"])
        key = User.create_secure_cache_key(identifier)

        cached = cache.get(key)
        visible = self.attribute_is_visible("showaddress")

        visible = self._current_user_override() or visible

        if cached and visible:
            logger.debug("Attribute 'address' of user {} loaded " "from cache.".format(self.id))
            return cached
        elif not cached and visible:
            c = LDAPConnection()
            try:
                results = c.user_attributes(self.dn, ['street', 'l', 'st', 'postalCode'])
                result = results.first_result()
                street = result['street'][0]
                city = result['l'][0]
                state = result['st'][0]
                postal_code = result['postalCode'][0]
            except KeyError:
                return None
            else:
                address_object = Address(street, city, state, postal_code)
                cache.set(key, address_object, timeout=settings.CACHE_AGE['user_attribute'])
                return address_object

        else:
            return None

    @property
    def birthday(self):
        """Returns a user's birthday.

        Returns:
            datetime object

        """
        identifier = ":".join([self.dn, "birthday"])
        key = User.create_secure_cache_key(identifier)

        cached = cache.get(key)
        visible = self.attribute_is_visible("showbirthday")

        if cached and visible:
            logger.debug("Attribute 'birthday' of user {} loaded " "from cache.".format(self.id))
            return cached
        elif not cached and visible:
            c = LDAPConnection()
            try:
                result = c.user_attributes(self.dn, ["birthday"])
                birthday = result.first_result()["birthday"][0]
            except KeyError:
                return None
            else:
                date_object = datetime.strptime(birthday, '%Y%m%d')
                cache.set(key, date_object, timeout=settings.CACHE_AGE['user_attribute'])
                return date_object

        else:
            return None

    @property
    def is_male(self):
        return self.sex.lower()[:1] == "m" if self.sex else False

    @property
    def is_female(self):
        return self.sex.lower()[:1] == "f" if self.sex else False

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

    def photo_binary(self, photo_year):
        """Returns the binary data for a user's picture.

        Returns:
            Binary data

        """
        identifier = ":".join([self.dn, "photo", photo_year])
        key = identifier  # User.create_secure_cache_key(identifier)

        cached = cache.get(key)

        if self.is_http_request_sender():
            visible = True
        elif self._current_user_override():
            visible = True
        else:
            perms = self.photo_permissions

            if perms["self"][photo_year] is None:
                visible_self = perms["self"]["default"]
            else:
                visible_self = perms["self"][photo_year]
            visible_parent = perms["parent"]

            visible = visible_self and visible_parent

        if cached and visible:
            logger.debug("{} photo of user {} loaded from cache.".format(photo_year.title(), self.id))
            return cached
        elif not cached and visible:
            c = LDAPConnection()
            dn = "cn={}Photo,{}".format(photo_year, self.dn)
            try:
                results = c.search(dn, "(objectClass=iodinePhoto)", ['jpegPhoto'])
                if len(results) == 1:
                    data = results[0]['attributes']['jpegPhoto'][0]
                    logger.debug("{} photo of user {} loaded from LDAP.".format(photo_year.title(), self.id))
                else:
                    data = None
            except (ldap3.LDAPNoSuchObjectResult, KeyError):
                data = None

            cache.set(key, data, timeout=settings.CACHE_AGE['ldap_permissions'])
            return data
        else:
            return None

    def photo_base64(self, photo_year):
        """Returns base64 encoded binary data for a user's picture.

        Returns:
            Base64 string, or None

        """
        binary = self.photo_binary(photo_year)
        if binary:
            return b64encode(binary)

        return None

    def default_photo(self):
        """Returns the default photo (in binary) that should be used.

        Returns:
            Binary data

        """
        data = None
        preferred = self.preferred_photo
        if preferred is not None:
            if preferred.endswith("Photo"):
                preferred = preferred[:-len("Photo")]

        if preferred == "AUTO" or preferred is None:
            if self.user_type == "tjhsstTeacher":
                current_grade = 12
            else:
                current_grade = int(self.grade)
                if current_grade > 12:
                    current_grade = 12

            for i in reversed(range(9, current_grade + 1)):
                data = self.photo_binary(Grade.names[i - 9])
                if data:
                    return data

        return None

    @property
    def photo_permissions(self):
        """Fetches the LDAP permissions for a user's photos.

        Returns:
            Dictionary

        """
        key = ":".join([self.dn, 'photo_permissions'])

        cached = cache.get(key)

        if cached:
            logger.debug("Photo permissions of user {} loaded " "from cache.".format(self.id))
            return cached
        else:
            c = LDAPConnection()

            perms = {"parent": False, "self": {"default": False, "freshman": None, "sophomore": None, "junior": None, "senior": None}}

            default_result = c.user_attributes(self.dn, ["perm-showpictures-self", "perm-showpictures"])
            default = default_result.first_result()
            if "perm-showpictures" in default:
                perms["parent"] = (default["perm-showpictures"][0] == "TRUE")

            if "perm-showpictures-self" in default:
                perms["self"]["default"] = (default["perm-showpictures-self"][0] == "TRUE")

            photos_result = c.search(self.dn, "(objectclass=iodinePhoto)", ["cn", "perm-showpictures", "perm-showpictures-self"])

            photos = photos_result

            for photo in photos:
                attrs = photo['attributes']
                grade = attrs["cn"][0][:-len("Photo")]
                try:
                    public = (attrs["perm-showpictures-self"][0] == "TRUE")
                    perms["self"][grade] = public
                except KeyError:
                    try:
                        public = (attrs["perm-showpictures"][0] == "TRUE")
                        perms["self"][grade] = public
                    except KeyError:
                        perms["self"][grade] = False

            cache.set(key, perms, timeout=settings.CACHE_AGE["ldap_permissions"])
            return perms

    @property
    def permissions(self):
        """Fetches the LDAP permissions for a user.

        Returns:
            Dictionary with keys "parent" and "self", each mapping to a
            list of permissions.

        """
        if self.dn is None:
            return None

        key = "{}:{}".format(self.dn, "user_info_permissions")

        cached = cache.get(key)

        if cached:
            logger.debug("Permissions of user {} loaded " "from cache.".format(self.id))
            return cached
        else:
            c = LDAPConnection()
            results = c.user_attributes(self.dn,
                                        ["perm-showaddress", "perm-showtelephone", "perm-showbirthday", "perm-showschedule", "perm-showeighth",
                                         "perm-showpictures", "perm-showaddress-self", "perm-showtelephone-self", "perm-showbirthday-self",
                                         "perm-showschedule-self", "perm-showeighth-self", "perm-showpictures-self"])
            result = results.first_result()
            perms = {"parent": {}, "self": {}}
            for perm, value in result.items():
                bool_value = True if (value[0] == 'TRUE') else False
                if perm.endswith("-self"):
                    perm_name = perm[5:-5]
                    perms["self"][perm_name] = bool_value
                else:
                    perm_name = perm[5:]
                    perms["parent"][perm_name] = bool_value

            cache.set(key, perms, timeout=settings.CACHE_AGE['ldap_permissions'])
            return perms

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
        """Checks if user has the admin permission 'printing'

        Returns:
            Boolean

        """

        return self.has_admin_permission('printing')

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

    @property
    def is_teacher(self):
        """Checks if user is a teacher.

        Returns:
            Boolean

        """

        return self.user_type == "tjhsstTeacher"

    @property
    def is_student(self):
        """Checks if user is a student.

        Returns:
            Boolean

        """

        return self.user_type == "tjhsstStudent"

    @property
    def is_senior(self):
        """Checks if user is a student in Grade 12.

        Returns:
            Boolean

        """
        return (self.is_student and self.grade and self.grade.number and self.grade.number == 12)

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

        return not self.username.startswith("INVALID_USER")

    @property
    def is_staff(self):
        """Checks if a user should have access to the Django Admin interface.

        This has nothing to do with staff at TJ - `is_staff`
        has to be overridden to make this a valid user model.

        Returns:
            Boolean

        """

        return self.is_superuser or self.member_of("admin_all")

    @property
    def is_attendance_user(self):
        """Checks if user is an attendance-only user.

        Returns:
            Boolean

        """

        return self.user_type == "tjhsstUser"

    @property
    def is_simple_user(self):
        """Checks if user is a simple user (e.g. eighth office user)

        Returns:
            Boolean

        """

        return self.user_type == "simpleUser"

    @property
    def is_attendance_taker(self):
        """Checks if user can take attendance for an eighth activity.

        Returns:
            Boolean

        """
        return (self.is_eighth_admin or self.is_teacher or self.is_attendance_user)

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
            requesting_user_id = request.user.id
            auth_backend = request.session["_auth_user_backend"]
            master_pwd_backend = "MasterPasswordAuthenticationBackend"

            return (str(requesting_user_id) == str(self.id) and not auth_backend.endswith(master_pwd_backend))
        except (AttributeError, KeyError):
            return False

    def attribute_is_visible(self, ldap_perm_name):
        """Checks if an attribute is visible to the public.

        Args:
            ldap_perm_name
                The name of the permission to check.

        Returns:
            Boolean

        """

        if ldap_perm_name == "specialPerm_studentID":
            try:
                # threadlocals is a module, not an actual thread locals object
                requesting_user = threadlocals.request().user
                return (requesting_user.is_teacher or requesting_user.is_simple_user)
            except (AttributeError, KeyError):
                return False
            return False

        perms = self.permissions

        if self.is_http_request_sender() or perms is None:
            return True
        else:
            public = True
            if ldap_perm_name in perms["parent"]:
                public = perms["parent"][ldap_perm_name]
            if ldap_perm_name in perms["self"]:
                public = public and perms["self"][ldap_perm_name]
            return public

    # Maps Python names for attributes to LDAP names and metadata
    ldap_user_attributes = {
        "ion_id": {
            "ldap_name": "iodineUidNumber",
            "perm": None,
            "is_list": False,
            "cache": True,
            "can_set": False
        },
        "ion_username": {
            "ldap_name": "iodineUid",
            "perm": None,
            "is_list": False,
            "cache": True,
            "can_set": False,
            "can_set": False
        },
        "student_id": {
            "ldap_name": "tjhsstStudentId",
            "perm": "specialPerm_studentID",
            "is_list": False,
            "cache": True,
            "can_set": True
        },
        "common_name": {
            "ldap_name": "cn",
            "perm": None,
            "is_list": False,
            "cache": True,
            "can_set": True
        },
        "display_name": {
            "ldap_name": "displayName",
            "perm": None,
            "is_list": False,
            "cache": True,
            "can_set": True
        },
        "nickname": {
            "ldap_name": "nickname",
            "perm": None,
            "is_list": False,
            "cache": True,
            "can_set": True
        },
        "title": {
            "ldap_name": "title",
            "perm": None,
            "is_list": False,
            "cache": True,
            "can_set": True
        },
        "first_name": {
            "ldap_name": "givenName",
            "perm": None,
            "is_list": False,
            "cache": True,
            "can_set": True
        },
        "middle_name": {
            "ldap_name": "middlename",
            "perm": None,
            "is_list": False,
            "cache": True,
            "can_set": True
        },
        "last_name": {
            "ldap_name": "sn",
            "perm": None,
            "is_list": False,
            "cache": True,
            "can_set": True
        },
        "sex": {
            "ldap_name": "gender",
            "perm": None,
            "is_list": False,
            "cache": True,
            "can_set": True
        },
        "user_type": {
            "ldap_name": "objectClass",
            "perm": None,
            "is_list": False,
            "cache": True,
            "can_set": False
        },
        "graduation_year": {
            "ldap_name": "graduationYear",
            "perm": None,
            "is_list": False,
            "cache": True,
            "can_set": False
        },
        "preferred_photo": {
            "ldap_name": "preferredPhoto",
            "perm": None,
            "is_list": False,
            "cache": True,
            "can_set": True
        },
        "emails": {
            "ldap_name": "mail",
            "perm": None,
            "is_list": True,
            "cache": True,
            "can_set": True
        },
        "home_phone": {
            "ldap_name": "homePhone",
            "perm": "showtelephone",
            "is_list": False,
            "cache": True,
            "can_set": True
        },
        "mobile_phone": {
            "ldap_name": "mobile",
            "perm": None,
            "is_list": False,
            "cache": True,
            "can_set": True
        },
        "other_phones": {
            "ldap_name": "telephoneNumber",
            "perm": None,
            "is_list": True,
            "cache": True,
            "can_set": True
        },
        "webpages": {
            "ldap_name": "webpage",
            "perm": None,
            "is_list": True,
            "cache": True,
            "can_set": True
        },
        "startpage": {
            "ldap_name": "startpage",
            "perm": None,
            "is_list": False,
            "cache": True,
            "can_set": True
        },
        "admin_comments": {
            "ldap_name": "eighthoffice-comments",
            "perm": None,
            "is_list": False,
            "cache": False,
            "can_set": True
        }
    }

    def __getattr__(self, name):
        """Return simple attributes of User.

        This is used to retrieve ldap fields that don't require special
        processing, e.g. email or graduation year. Fields names are
        mapped to more user friendly names to increase readability of
        templates. When more complex processing is required or a complex
        return type is required, (such as a datetime object for a
        birthday), properties should be used instead.

        Note that __getattr__ is used instead of __getattribute__ so the
        method is called after checking regular attributes instead of
        before.

        Returns:
            Either a list of strings or a string, depending on
            the attribute fetched.

        """

        if name not in User.ldap_user_attributes:
            # If the property raises an AttributeError, __getattribute__ falls back to __getattr__, hence this special case.
            if isinstance(User.__dict__.get(name), property):
                return User.__dict__.get(name).fget(self)
            raise AttributeError("'User' has no attribute '{}'".format(name))

        if self.dn is None:
            if not self.is_active:
                return None

            raise exceptions.ObjectDoesNotExist("Could not determine DN of User with ID {} (requesting {})".format(self.id, name))

        attr = User.ldap_user_attributes[name]
        should_cache = attr["cache"]
        if should_cache:
            identifier = ":".join((self.dn, name))
            key = User.create_secure_cache_key(identifier)

            cached = cache.get(key)
        else:
            cached = False

        if attr["perm"] is None:
            visible = True
        else:
            visible = self.attribute_is_visible(attr["perm"])

        if name not in ["ion_id", "ion_username", "user_type"]:
            visible = self._current_user_override() or visible

        if cached and visible:
            logger.debug("Attribute '{}' of user {} loaded " "from cache.".format(name, self.id or self.dn))
            return cached
        elif not cached and visible:
            c = LDAPConnection()
            field_name = attr["ldap_name"]
            try:
                results = c.user_attributes(self.dn, [field_name])
                try:
                    result = results.first_result()[field_name]
                except TypeError:
                    result = None

                if attr["is_list"]:
                    value = result
                elif result:
                    value = result[0]
                else:
                    value = None
                    should_cache = False

                if should_cache:
                    cache.set(key, value, timeout=settings.CACHE_AGE["user_attribute"])
                return value
            except KeyError:
                return None
        else:
            return None

    def set_ldap_attribute(self, name, value, override_set=False):
        """Set a user attribute in LDAP."""

        if name not in User.ldap_user_attributes:
            raise Exception("Can not set User attribute '{}' -- not in user attribute list.".format(name))

        if User.ldap_user_attributes[name]["can_set"]:
            pass
        elif override_set:
            pass
        else:
            raise Exception("Not allowed to set User attribute '{}'".format(name))

        if self.dn is None:
            raise Exception("Could not determine DN of User")

        attr = User.ldap_user_attributes[name]
        should_cache = attr["cache"]

        if attr["is_list"] and not isinstance(value, (list, tuple)):
            raise Exception("Expected list for attribute '{}'".format(name))

        field_name = attr["ldap_name"]
        self.set_raw_ldap_attribute(field_name, value)

        if should_cache:
            identifier = ":".join((self.dn, name))
            key = User.create_secure_cache_key(identifier)
            cache.set(key, value, timeout=settings.CACHE_AGE["user_attribute"])

    def set_ldap_preference(self, item_name, value, is_admin=False):
        logger.debug("Pref: {} {}".format(item_name, value))

        if item_name.endswith("-self"):
            field_name = item_name.split("-self")[0]
            field_type = "self"
            ldap_name = field_name + "self"
        elif item_name.endswith("self"):
            field_name = item_name.split("self")[0]
            field_type = "self"
            ldap_name = field_name + "self"
        else:
            field_name = item_name
            field_type = "parent"
            ldap_name = field_name

        if field_type == "parent" and not is_admin:
            raise Exception("You do not have permission to change this parent field.")

        if value is True:
            value = "TRUE"

        if value is False:
            value = "FALSE"

        if item_name.startswith("photoperm-"):
            grade = field_name.split("photoperm-")[1]
            self.set_raw_ldap_photoperm(field_type, grade, value)
            cache.delete(":".join([self.dn, "photo_permissions"]))
        else:
            logger.debug("Setting raw LDAP: {} = {}".format(ldap_name, value))
            self.set_raw_ldap_attribute(ldap_name, value)

        if field_name == "showpictures":
            cache.delete(":".join([self.dn, "photo_permissions"]))

        if field_name in ["showschedule", "showaddress", "showphone", "showbirthday", "showpictures", "showeighth"]:
            cache.delete(":".join([self.dn, "user_info_permissions"]))

    def set_raw_ldap_photoperm(self, field_type, grade, value):
        if self.dn is None:
            raise Exception("Could not determine DN of User")

        if field_type not in ["parent", "self"]:
            raise Exception("Invalid photo field type")

        photo_dn = "cn={}Photo,{}".format(grade, self.dn)
        photo_field = "perm-showpictures" + ("-self" if field_type == "self" else "")

        c = LDAPConnection()
        logger.info("SET {}: {} = {}".format(photo_dn, photo_field, value))
        c.set_attribute(photo_dn, photo_field, value)

    def set_raw_ldap_attribute(self, field_name, value):
        """Set a raw user attribute in LDAP."""
        if self.dn is None:
            raise Exception("Could not determine DN of User")

        c = LDAPConnection()
        logger.info("SET {}: {} = {}".format(self.dn, field_name, value))
        c.set_attribute(self.dn, field_name, value)

    def clear_cache(self):
        logger.debug("Clearing LDAP user cache for {}".format(self.dn))
        for attr in User.ldap_user_attributes:
            cache.delete(":".join((self.dn, attr)))
            cache.delete(User.create_secure_cache_key(":".join((self.dn, attr))))

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

    def __str__(self):
        return self.username or self.ion_username or self.id

    def __int__(self):
        return self.id


class Class(object):
    """Represents a tjhsstClass LDAP object in which a user is enrolled.

    Note that this is not a Django model, but rather an interface
    to LDAP classes.

    Attributes:
        dn
            The DN of the cooresponding tjhsstClass in LDAP
        section_id
            The section ID of the class

    """

    def __init__(self, dn=None, id=None):
        """Initialize the Class object.

        Either dn or id is required.

        Args:
            dn
                The full DN of the class.
            id
                The tjhsstSectionId of the class.

        """
        self.dn = dn or 'tjhsstSectionId={},ou=schedule,dc=tjhsst,dc=edu'.format(id)

    @property
    def section_id(self):
        return ldap3.utils.dn.parse_dn(self.dn)[0][1]

    pk = section_id

    @property
    def students(self):
        """Returns a list of students in the class. This may not always return all of the actual
        students if you do not have permission to view that information.

        Returns:
            List of user objects

        """
        c = LDAPConnection()
        students = c.search(settings.USER_DN, "enrolledClass={}".format(self.dn), ["dn"])

        users = []
        for row in students:
            dn = row["dn"]
            try:
                user = User.get_user(dn=dn)
            except User.DoesNotExist:
                continue
            users.append(user)

        return users

    @property
    def teacher(self):
        """Returns the teacher/sponsor of the class.

        Returns:
            User object

        """
        key = ":".join([self.dn, 'teacher'])

        cached = cache.get(key)

        if cached:
            logger.debug("Attribute 'teacher' of class {} loaded " "from cache.".format(self.section_id))
            return User.get_user(dn=cached)
        else:
            c = LDAPConnection()
            result = c.class_attributes(self.dn, ['sponsorDn']).first_result()
            if not result:
                return None
            dn = result['sponsorDn'][0]

            # Only cache the dn, since pickling would recursively fetch
            # all of the properties and quickly reach the maximum
            # recursion depth
            cache.set(key, dn, timeout=settings.CACHE_AGE['class_teacher'])
            return User.get_user(dn=dn)

    @property
    def quarters(self):
        """Returns the quarters a class is in session.

        Returns:
            Integer list

        """
        key = ":".join([self.dn, "quarters"])

        cached = cache.get(key)

        if cached:
            logger.debug("Attribute 'quarters' of class {} loaded from cache.".format(self.section_id))
            return cached
        else:
            c = LDAPConnection()
            result = c.class_attributes(self.dn, ["quarterNumber"]).first_result()
            if not result:
                return None
            result = [int(i) for i in result["quarterNumber"]]

            cache.set(key, result, timeout=settings.CACHE_AGE["class_attribute"])
            return result

    @property
    def sortvalue(self):
        """Returns the sort value of this class.

        This can be derived from the following formula:
            Minimum Period + Sum of values of quarters / 11

        We divide by 11 because the maximum sum is 10 and we want the
        quarters to be a secondary sort.

        Returns:
            A float value of the equation.

        """
        return min(map(float, self.periods)) + (float(sum(self.quarters)) / 11)

    @property
    def sections(self):
        """Returns a list of other Class objects which are of the same class type.

        Returns:
            A list of class objects.

        """
        class_sections = ClassSections(id=self.class_id)

        schedule = []
        classes = class_sections.classes
        # Sort in order
        for class_object in classes:
            sortvalue = class_object.sortvalue
            schedule.append((sortvalue, class_object))

        ordered_schedule = sorted(schedule, key=lambda e: e[0])
        if ordered_schedule:
            return list(zip(*ordered_schedule))[1]  # The class objects
        else:
            return []

    def __getattr__(self, name):
        """Return simple attributes of Class.

        This is used to retrieve ldap fields that don't require special
        processing, e.g. roomNumber or period. Fields names are
        mapped to more user friendly names to increase readability of
        templates. When more complex processing is required or a
        complex return type is required, (such as a Class object),
        properties should be used instead.

        Note that __getattr__ is used instead of __getattribute__ so
        the method is called after checking regular attributes instead
        of before.

        This method should not be called directly - use dot notation or
        getattr() to fetch an attribute.

        Args:
            name
                The string name of the attribute.

        Returns:
            Either a list of strings or a string, depending on the attribute fetched.

        """

        class_attributes = {
            "name": {
                "ldap_name": "cn",
                "is_list": False
            },
            "periods": {
                "ldap_name": "classPeriod",
                "is_list": True  # Some classes run for two periods
            },
            "class_id": {
                "ldap_name": "tjhsstClassId",
                "is_list": False
            },
            "course_length": {
                "ldap_name": "courseLength",
                "is_list": False
            },
            "room_number": {
                "ldap_name": "roomNumber",
                "is_list": False
            }
        }

        if name not in class_attributes:
            raise AttributeError("'Class' has no attribute '{}'".format(name))

        key = ":".join([self.dn, name])

        cached = cache.get(key)

        if cached:
            logger.debug("Attribute '{}' of class {} loaded " "from cache.".format(name, self.section_id))
            return cached
        else:
            c = LDAPConnection()
            attr = class_attributes[name]
            field_name = attr["ldap_name"]
            try:
                result = c.class_attributes(self.dn, [field_name]).first_result()
                if result:
                    result = result[field_name]
                else:
                    return None
            except KeyError:
                logger.warning("KeyError fetching " + name + " for class " + self.dn)
                return None
            else:
                if attr["is_list"]:
                    value = result
                    if name == "periods":
                        value = sorted(list(map(int, value)))
                else:
                    value = result[0]

                cache.set(key, value, timeout=settings.CACHE_AGE['class_attribute'])
                return value

    @property
    def period(self):
        return ", ".join([str(i) for i in self.periods])

    def __str__(self):
        if self.name and self.teacher.last_name:
            return "{}, Period {} ({})".format(self.name, self.period, self.teacher.last_name)
        return "{}".format(self.dn)


class ClassSections(object):
    """Represents a list of tjhsstClass LDAP objects.

    Note that this is not a Django model, but rather an interface
    to LDAP classes.

    Attributes:
        class_id
            The class ID of the class(es) (tjhsstClassId)

    """

    def __init__(self, dn=None, id=None):
        """Initialize the Class object.

        Either dn or id is required.

        Args:
            id
                The tjhsstClassId of the class.

        """
        self.dn = dn or "ou=schedule,dc=tjhsst,dc=edu"
        self.id = id

    @property
    def classes(self):
        """Returns a list of classes sections for the given class.

        Returns:
            List of Class objects

        """
        c = LDAPConnection()
        query = c.search(self.dn, "(&(objectClass=tjhsstClass)(tjhsstClassId={}))".format(self.id), ["tjhsstSectionId", "dn"])

        classes = []
        for row in query:
            dn = row["dn"]
            c = Class(dn=dn)
            classes.append(c)

        return classes

    def __str__(self):
        if self.classes:
            return "{}".format(self.classes[0].name)

        return "{}".format(self.id)


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
        if today.month >= 7:
            current_senior_year = today.year + 1
        else:
            current_senior_year = today.year

        return current_senior_year - graduation_year + 12

    @classmethod
    def year_from_grade(cls, grade):
        today = datetime.now()
        if today.month >= 7:
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
