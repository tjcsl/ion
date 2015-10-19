# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime
import hashlib
import logging
import ldap
import os
import re
from django.db import models
from django.conf import settings
from django.core.cache import cache
from django.core import exceptions
from django.contrib.auth.models import (
    AbstractBaseUser, PermissionsMixin, UserManager)
from django.core.signing import Signer
from intranet.db.ldap_db import LDAPConnection, LDAPFilter
from intranet.middleware import threadlocals
from ..groups.models import Group

logger = logging.getLogger(__name__)


class UserManager(UserManager):

    """User model Manager for table-level User queries.

    Provides table-level LDAP abstraction for the User model. If a call
    to a method fails for this Manager, the call is deferred to the
    default User model manager.

    """

    def user_with_student_id(self, student_id):
        """Get a unique user object by student ID."""
        c = LDAPConnection()

        results = c.search(settings.USER_DN,
                           "tjhsstStudentId={}".format(student_id),
                           ["dn"])

        if len(results) == 1:
            return User.get_user(dn=results[0][0])
        return None

    def user_with_ion_id(self, student_id):
        """Get a unique user object by Ion ID."""
        c = LDAPConnection()

        results = c.search(settings.USER_DN,
                           "iodineUidNumber={}".format(student_id),
                           ["dn"])

        if len(results) == 1:
            return User.get_user(dn=results[0][0])
        return None


    def _ldap_and_string(self, opts):
        """Combine LDAP queries with AND

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


        if sn and not given_name:
            results = c.search(settings.USER_DN,
                           "sn={}".format(sn),
                           ["dn"])
        elif given_name:
            query = ["givenName={}".format(given_name)]
            if sn:
                query.append("sn={}".format(sn))
            results = c.search(settings.USER_DN,
                               self._ldap_and_string(query),
                               ["dn"])
        
            if len(results) == 0:
                # Try their first name as a nickname
                query[0] = "nickname={}".format(given_name)
                results = c.search(settings.USER_DN,
                                   self._ldap_and_string(query),
                                   ["dn"])

        if len(results) == 1:
            return User.get_user(dn=results[0][0])

        return None

    def users_with_birthday(self, month, day):
        """Return a list of user objects who have a birthday on a given date."""
        c = LDAPConnection()

        month = int(month)
        if month < 10:
            month = "0"+str(month)

        day = int(day)
        if day < 10:
            day = "0"+str(day)

        search_query = "birthday=*{}{}".format(month, day)
        results = c.search(settings.USER_DN,
                        search_query,
                        ["dn"])

        users = []
        for res in results:
            users.append(User.get_user(dn=res[0]))


        return users

    # Simple way to filter out teachers and students without hitting LDAP.
    # This shouldn't be a problem unless the username scheme changes and
    # the consequences of error are not significant.

    def get_students(self):
        """Get user objects that are students (quickly)."""
        key = "users:students"
        cached = cache.get(key)
        if cached:
            logger.debug("Using cached User.get_students")
            return cached
        else:
            usernonums = User.objects.filter(username__startswith="2")
            # Add possible exceptions handling here
            logger.debug("Set cache for User.get_students")
            cache.set(key, usernonums, timeout=settings.CACHE_AGE['users_list'])
            return usernums


    def get_teachers(self):
        """Get user objects that are teachers (quickly)."""
        key = "users:teachers"
        cached = cache.get(key)
        if cached:
            logger.debug("Using cached User.get_teachers")
            return cached
        else:
            usernonums = User.objects.exclude(username__startswith="2")
            # Add possible exceptions handling here
            usernonums = usernonums | User.objects.filter(id=31863)
            logger.debug("Set cache for User.get_teachers")
            cache.set(key, usernonums, timeout=settings.CACHE_AGE['users_list'])
            return usernonums

    def get_teachers_sorted(self):
        """Get teachers sorted by last name."""
        teachers = self.get_teachers()
        teachers = [(u.last_name, u.first_name, u.id) for u in teachers]
        teachers.sort(key=lambda u: (u[0], u[1]))
        for t in teachers:
            if t[0] is None or t[0] == u"." or t[0] == ".":
                teachers.remove(t)
        # Hack to return QuerySet in given order
        id_list = [t[2] for t in teachers]
        clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(id_list)])
        ordering = 'CASE %s END' % clauses
        queryset = User.objects.filter(id__in=id_list).extra(
            select={'ordering': ordering}, order_by=('ordering',))
        return queryset



class User(AbstractBaseUser, PermissionsMixin):

    """Django User model subclass with properties that fetch data from
    LDAP

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

    # Private dn cache
    _dn = None

    # Required to replace the default Django User model
    USERNAME_FIELD = "username"

    """Override default Model Manager (objects) with
    custom UserManager to add table-level functionality."""
    objects = UserManager()

    @classmethod
    def get_user(cls, dn=None, id=None, username=None):
        """Retrieve a user object from LDAP and save it to the SQL
        database if necessary.

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
                    raise User.DoesNotExist(
                        "`User` with ID {} does not exist.".format(id)
                    )

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
                    user.username = user.ion_username

                    user.set_unusable_password()
                    user.last_login = datetime(9999, 1, 1)

                    user.save()
            except (ldap.INVALID_DN_SYNTAX, ldap.NO_SUCH_OBJECT):
                raise User.DoesNotExist(
                    "`User` with DN '{}' does not exist.".format(dn)
                )
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
            logger.debug("DN of User with ID {} loaded "
                         "from cache.".format(id))
            return cached
        else:
            c = LDAPConnection()
            result = c.search(settings.USER_DN,
                              "iodineUidNumber={}".format(id),
                              ['dn'])
            if len(result) == 1:
                dn = result[0][0]
            else:
                logger.debug("No such User with ID {}.".format(id))
                dn = None
            cache.set(key, dn, timeout=settings.CACHE_AGE['dn_id_mapping'])
            return dn

    @staticmethod
    def dn_from_username(username):
        # logger.debug("Fetching DN of User with username {}.".format(username))
        return "iodineUid=" + ldap.dn.escape_dn_chars(username) + "," + settings.USER_DN

    @staticmethod
    def username_from_dn(dn):
        # logger.debug("Fetching username of User with ID {}.".format(id))
        return ldap.dn.str2dn(dn)[0][0][1]

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
        hash = hashlib.sha1(signed)
        return hash.hexdigest()

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
        """Returns whether a user has an admin permission (explicitly,
        or implied by being in the "admin_all" group)

        Returns:
            Boolean

        """

        if perm == "ldap":
            # not all of admin_all has LDAP permissions
            return self.member_of("admin_ldap")

        return self.member_of("admin_all") or self.member_of("admin_" + perm)

    @property
    def full_name(self):
        """Return full name, e.g. Angela William. This is required
        for subclasses of User."""
        return self.common_name

    @property
    def display_name(self):
        display_name = self.__getattr__("display_name")
        if not display_name:
            return self.full_name
        return display_name

    property
    def last_first(self):
        """Return a name in the format of:
            Lastname, Firstname [(Nickname)]
        """
        return ("{}, {} ".format(self.last_name, self.first_name) +
               ("({})".format(self.nickname) if self.nickname else ""))


    @property
    def last_first_id(self):
        """Return a name in the format of:
            Lastname, Firstname [(Nickname)] (Student ID/ID/Username)
        """
        return ("{}{} ".format(self.last_name, ", " + self.first_name if self.first_name else "") +
               ("({}) ".format(self.nickname) if self.nickname else "") +
               ("({})".format(self.student_id if self.is_student and self.student_id else self.username)))

    @property
    def last_first_initial(self):
        """Return a name in the format of:
            Lastname, F [(Nickname)]
        """
        return ("{}{} ".format(self.last_name, ", " + self.first_name[:1] + "." if self.first_name else "") +
               ("({}) ".format(self.nickname) if self.nickname else ""))

    @property
    def short_name(self):
        """Return short name (first name) of a user. This is required
        for subclasses of User.
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
        """Set DN for a user.
        """
        if not self._dn:
            self._dn = dn
        # if not self.username:
            # self.username = ldap.dn.str2dn(dn)[0][0][1]

    @property
    def tj_email(self):
        """
        Get (or guess) a user's TJ email. If a fcps.edu or
        tjhsst.edu email is specified in their email list, use
        that. Otherwise, append the user's username to the proper
        email suffix, depending on whether they are a student or teacher.
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
        key = ":".join([self.dn, 'grade'])

        cached = cache.get(key)

        if cached:
            logger.debug("Grade of user {} loaded "
                         "from cache.".format(self.id))
            return cached
        else:
            grad_year = self.graduation_year
            if not grad_year:
                grade = None
            else:
                grade = Grade(grad_year)

            cache.set(key, grade,
                      timeout=settings.CACHE_AGE['ldap_permissions'])
            return grade

    @property
    def classes(self):
        """Returns a list of Class objects for a user ordered by
        period number.

        Returns:
            List of Class objects

        """
        is_student = self.is_student

        identifier = ":".join([self.dn, "classes"])
        key = User.create_secure_cache_key(identifier)

        cached = cache.get(key)
        if is_student:
            visible = self.attribute_is_visible("showschedule")
        else:
            visible = True

        if cached and visible:
            logger.debug("Attribute 'classes' of user {} loaded "
                         "from cache.".format(self.id))
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
                    query = LDAPFilter.and_filter(
                        "objectClass=tjhsstClass",
                        "sponsorDn=" + self.dn
                    )
                    results = c.search(settings.CLASS_DN, query, ["dn"])
                    classes = [r[0] for r in results]

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
                dn_list = list(zip(*ordered_schedule)[2])
                cache.set(key, dn_list,
                          timeout=settings.CACHE_AGE['user_classes'])
                return list(zip(*ordered_schedule)[1])  # Unpacked class list
        else:
            return None

    @property
    def counselor(self):
        """Returns a user's counselor as a User object.

        Returns:
            :class:`User` object for the user's counselor

        """
        key = ":".join([self.dn, "counselor"])

        cached = cache.get(key)

        if cached:
            logger.debug("Attribute 'counselor' of user {} loaded "
                         "from cache.".format(self.id))
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
                cache.set(key, counselor,
                          timeout=settings.CACHE_AGE['user_attribute'])
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

        if cached and visible:
            logger.debug("Attribute 'address' of user {} loaded "
                         "from cache.".format(self.id))
            return cached
        elif not cached and visible:
            c = LDAPConnection()
            try:
                results = c.user_attributes(self.dn,
                                            ['street', 'l', 'st', 'postalCode'])
                result = results.first_result()
                street = result['street'][0]
                city = result['l'][0]
                state = result['st'][0]
                postal_code = result['postalCode'][0]
            except KeyError:
                return None
            else:
                address_object = Address(street, city, state, postal_code)
                cache.set(key, address_object,
                          timeout=settings.CACHE_AGE['user_attribute'])
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
            logger.debug("Attribute 'birthday' of user {} loaded "
                         "from cache.".format(self.id))
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
                cache.set(key, date_object,
                          timeout=settings.CACHE_AGE['user_attribute'])
                return date_object

        else:
            return None

    @property
    def age(self, date=None):
        """Returns a user's age, based on their birthday.
           Optional date argument to find their age on a given day.

        Returns:
            integer

        """
        if not date:
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
        else:
            perms = self.photo_permissions

            if perms["self"][photo_year] is None:
                visible_self = perms["self"]["default"]
            else:
                visible_self = perms["self"][photo_year]
            visible_parent = perms["parent"]

            visible = visible_self and visible_parent

        if cached and visible:
            logger.debug("{} photo of user {} loaded "
                         "from cache.".format(photo_year.title(),
                                              self.id))
            return cached
        elif not cached and visible:
            c = LDAPConnection()
            dn = "cn={}Photo,{}".format(photo_year, self.dn)
            try:
                results = c.search(dn,
                                   "(objectClass=iodinePhoto)",
                                   ['jpegPhoto'])
                if len(results) == 1:
                    data = results[0][1]['jpegPhoto'][0]
                else:
                    data = None
            except (ldap.NO_SUCH_OBJECT, KeyError):
                data = None

            cache.set(key, data,
                      timeout=settings.CACHE_AGE['ldap_permissions'])
            return data
        else:
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
            logger.debug("Photo permissions of user {} loaded "
                         "from cache.".format(self.id))
            return cached
        else:
            c = LDAPConnection()

            perms = {
                "parent": False,
                "self": {
                    "default": False,
                    "freshman": None,
                    "sophomore": None,
                    "junior": None,
                    "senior": None
                }
            }

            default_result = c.user_attributes(self.dn,
                                               ["perm-showpictures-self",
                                                "perm-showpictures"])
            default = default_result.first_result()
            if "perm-showpictures" in default:
                perms["parent"] = (default["perm-showpictures"][0] == "TRUE")

            if "perm-showpictures-self" in default:
                perms["self"]["default"] = (
                    default["perm-showpictures-self"][0] == "TRUE"
                )

            photos_result = c.search(self.dn,
                                     "(objectclass=iodinePhoto)",
                                     ["cn",
                                      "perm-showpictures",
                                      "perm-showpictures-self"])

            photos = photos_result

            for dn, attrs in photos:
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

            cache.set(key, perms,
                      timeout=settings.CACHE_AGE["ldap_permissions"])
            return perms

    @property
    def permissions(self):
        """Fetches the LDAP permissions for a user.

        Returns:
            Dictionary with keys "parent" and "self", each mapping to a
            list of permissions.
        """
        if self.dn is None:
            return False

        key = "{}:{}".format(self.dn, "user_info_permissions")

        cached = cache.get(key)

        if cached:
            logger.debug("Permissions of user {} loaded "
                         "from cache.".format(self.id))
            return cached
        else:
            c = LDAPConnection()
            results = c.user_attributes(self.dn, ["perm-showaddress",
                                                  "perm-showtelephone",
                                                  "perm-showbirthday",
                                                  "perm-showschedule",
                                                  "perm-showeighth",
                                                  "perm-showpictures",
                                                  "perm-showaddress-self",
                                                  "perm-showtelephone-self",
                                                  "perm-showbirthday-self",
                                                  "perm-showschedule-self",
                                                  "perm-showeighth-self",
                                                  "perm-showpictures-self"
                                                  ])
            result = results.first_result()
            perms = {"parent": {}, "self": {}}
            for perm, value in result.iteritems():
                bool_value = True if (value[0] == 'TRUE') else False
                if perm.endswith("-self"):
                    perm_name = perm[5:-5]
                    perms["self"][perm_name] = bool_value
                else:
                    perm_name = perm[5:]
                    perms["parent"][perm_name] = bool_value

            cache.set(key, perms,
                      timeout=settings.CACHE_AGE['ldap_permissions'])
            return perms

    @property
    def can_view_eighth(self):
        """Checks if a user has the showeighth permission.

        Returns:
            Boolean

        """

        return (self.permissions["self"]["showeighth"] if (
                    self.permissions and
                    "self" in self.permissions and
                    "showeighth" in self.permissions["self"]
                ) else False)

    @property
    def is_eighth_admin(self):
        """Checks if user is an eighth period admin.

        Returns:
            Boolean

        """

        return self.has_admin_permission('eighth')

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
        """Checks if a user should have access to the Django Admin
        interface. This has nothing to do with staff at TJ - `is_staff`
        has to be overridden to make this a valid user model.

        Returns:
            Boolean

        """

        return self.is_superuser

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
        return (self.is_eighth_admin or
                self.is_teacher or
                self.is_attendance_user)

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

            return (str(requesting_user_id) == str(self.id) and
                    not auth_backend.endswith(master_pwd_backend))
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
                return (requesting_user.is_teacher or
                        requesting_user.is_simple_user)
            except (AttributeError, KeyError):
                return False
            return False

        perms = self.permissions

        if self.is_http_request_sender():
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
        """Return simple attributes of User

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

        if cached and visible:
            logger.debug("Attribute '{}' of user {} loaded "
                         "from cache.".format(name, self.id or self.dn))
            return cached
        elif not cached and visible:
            c = LDAPConnection()
            field_name = attr["ldap_name"]
            try:
                results = c.user_attributes(self.dn, [field_name])
                result = results.first_result()[field_name]

                if attr["is_list"]:
                    value = result
                else:
                    value = result[0]

                if should_cache:
                    cache.set(key, value,
                              timeout=settings.CACHE_AGE["user_attribute"])
                return value
            except KeyError:
                return None
        else:
            return None

    def set_ldap_attribute(self, name, value, override_set=False):
        """Set a user attribute in LDAP.
        """
        if name not in User.ldap_user_attributes:
            raise Exception("Can not set User attribute '{}' -- not in user attribute list.".format(name))
        if not User.ldap_user_attributes[name]["can_set"] and not override_set:
            raise Exception("Not allowed to set User attribute '{}'".format(name))

        if self.dn is None:
            raise Exception("Could not determine DN of User")

        attr = User.ldap_user_attributes[name]
        should_cache = attr["cache"]

        if attr["is_list"] and not isinstance(value, (list, tuple)):
            raise Exception("Expected list for attribute '{}'".format(name))

        # Possible issue with python ldap with unicode values
        if isinstance(value, (unicode, str)):
            value = str(value)

        c = LDAPConnection()
        field_name = attr["ldap_name"]
        c.set_attribute(self.dn, field_name, value)

        if should_cache:
            identifier = ":".join((self.dn, name))
            key = User.create_secure_cache_key(identifier)
            cache.set(key, value, timeout=settings.CACHE_AGE["user_attribute"])

    def set_raw_ldap_attribute(self, field_name, value):
        """Set a raw user attribute in LDAP.
        """
        if self.dn is None:
            raise Exception("Could not determine DN of User")

        # Possible issue with python ldap with unicode values
        if isinstance(value, (unicode, str)):
            value = str(value)

        c = LDAPConnection()
        c.set_attribute(self.dn, field_name, value)

    def clear_cache(self):
        logger.debug("Clearing LDAP user cache for {}".format(self.dn))
        for attr in User.ldap_user_attributes:
            cache.delete(":".join((self.dn, attr)))
            cache.delete(User.create_secure_cache_key(":".join((self.dn, attr))))

    @property
    def is_eighth_sponsor(self):
        """Determine whether the given user is associated with an
        :class:`EighthSponsor` and, therefore, should view activity
        sponsoring information.

        """

        from ..eighth.models import EighthSponsor

        return EighthSponsor.objects.filter(user=self).exists()

    def get_eighth_sponsor(self):
        """Return the :class:`EighthSponsor` that a given user is
        associated with.
        """

        from ..eighth.models import EighthSponsor

        try:
            sp = EighthSponsor.objects.get(user=self)
        except EighthSponsor.DoesNotExist:
            return False

        return sp

    def absence_count(self):
        """Return the user's absence count. If the user has no absences
        or is not a signup user, returns 0.

        """
        from ..eighth.models import EighthSignup

        return EighthSignup.objects.filter(user=self, was_absent=True, scheduled_activity__attendance_taken=True).count()

    def __unicode__(self):
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

    section_id = property(lambda c: ldap.dn.str2dn(c.dn)[0][0][1])
    pk = section_id

    @property
    def students(self):
        """Returns a list of students in the class.
        This may not always return all of the actual students if you do
        not have permission to view that information.

        Returns:
            List of user objects

        """
        c = LDAPConnection()
        students = c.search(settings.USER_DN, "enrolledClass={}".format(self.dn), [])

        users = []
        for row in students:
            dn = row[0]
            try:
                user = User.get_user(dn=dn)
            except User.DoesNotExist:
                continue
            users.append(user)

        return users

    @property
    def teacher(self):
        """Returns the teacher/sponsor of the class

        Returns:
            User object

        """
        key = ":".join([self.dn, 'teacher'])

        cached = cache.get(key)

        if cached:
            logger.debug("Attribute 'teacher' of class {} loaded "
                         "from cache.".format(self.section_id))
            return User.get_user(dn=cached)
        else:
            c = LDAPConnection()
            results = c.class_attributes(self.dn, ['sponsorDn'])
            result = results.first_result()
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
            logger.debug("Attribute 'quarters' of class {} loaded "
                         "from cache.".format(self.section_id))
            return cached
        else:
            c = LDAPConnection()
            results = c.class_attributes(self.dn, ["quarterNumber"])
            result = [int(i) for i in results.first_result()["quarterNumber"]]

            cache.set(key, result,
                      timeout=settings.CACHE_AGE["class_attribute"])
            return result

    @property
    def sortvalue(self):
        """Returns the sort value of this class

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
        """Returns a list of other Class objects which are of
           the same class type.

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
        return list(zip(*ordered_schedule)[1]) # The class objects
    

    def __getattr__(self, name):
        """Return simple attributes of Class

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
            logger.debug("Attribute '{}' of class {} loaded "
                         "from cache.".format(name, self.section_id))
            return cached
        else:
            c = LDAPConnection()
            attr = class_attributes[name]
            field_name = attr["ldap_name"]
            try:
                results = c.class_attributes(self.dn, [field_name])
                result = results.first_result()[field_name]
            except KeyError:
                logger.warning("KeyError fetching " + name +
                               " for class " + self.dn)
                return None
            else:
                if attr["is_list"]:
                    value = result
                    if name == "periods":
                        value = sorted(list(map(int, value)))
                else:
                    value = result[0]

                cache.set(key, value,
                          timeout=settings.CACHE_AGE['class_attribute'])
                return value

    def __unicode__(self):
        return "{} ({})".format(self.name, self.teacher.last_name) or self.dn

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
        query = c.search(self.dn, "(&(objectClass=tjhsstClass)(tjhsstClassId={}))".format(self.id), ["tjhsstSectionId"])

        classes = []
        for row in query:
            dn = row[0]
            c = Class(dn=dn)
            classes.append(c)

        return classes

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

    def __unicode__(self):
        """Returns full address string."""
        return "{}\n{}, {} {}".format(self.street, self.city,
                                      self.state, self.postal_code)


class Grade(object):

    """Represents a user's grade."""
    names = ["freshman", "sophomore", "junior", "senior"]

    def __init__(self, graduation_year):
        """Initialize the Grade object.

        Args:
            graduation_year
                The numerical graduation year of the user
        """
        self._year = int(graduation_year)
        today = datetime.now()
        if today.month >= 7:
            current_senior_year = today.year + 1
        else:
            current_senior_year = today.year

        self._number = current_senior_year - self._year + 12

        if 9 <= self._number <= 12:
            self._name = Grade.names[self._number - 9]
        else:
            self._name = "graduate"

        if self._number is None:
            self._number = 13


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
    def text(self):
        """Return the grade's number as a string (e.g. Grade 12, Graduate)"""
        if 9 <= self._number <= 12:
            return "Grade {}".format(self._number)
        else:
            return self._name
    

    def __int__(self):
        """Return the grade as a number (9-12)."""
        return self._number

    def __unicode__(self):
        """Return name of the grade."""
        return self._name

    def __str__(self):
        return self.__unicode__()
