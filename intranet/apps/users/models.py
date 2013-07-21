import logging
import datetime
import ldap
import hashlib
from intranet.db.ldap_db import LDAPConnection
from intranet import settings
from intranet.middleware import threadlocals
from django.db import models
from django import template
from django.core.cache import cache
from django.contrib.auth.models import AbstractBaseUser
from django.core.signing import Signer

logger = logging.getLogger(__name__)
register = template.Library()


class UserManager(models.Manager):
    """User model Manager for table-level LDAP queries.

    Provides table-level LDAP abstraction for the User model. If a call
    to a method fails for this Manager, the call is deferred to the
    default User model manager.

    """
    def return_something(self):
        return "something"


class User(AbstractBaseUser):
    """Django User model subclass with properties that fetch data from LDAP

    Represents a tjhsstStudent or tjhsstTeacher LDAP object.Extends
    AbstractBaseUser so the model will work with Django's built-in
    authorization functionality.

    """
    # Django Model Fields
    username = models.CharField(max_length=50, unique=True, db_index=True)

    # first_name = models.CharField(max_length=50)
    # last_name = models.CharField(max_length=50)

    """Required to replace the default Django User model."""
    USERNAME_FIELD = 'username'

    """Override default Model Manager (objects) with
    custom UserManager."""
    objects = UserManager()

    @classmethod
    def create(cls, dn=None, id=None):
        """User factory method.

        Creates a User method from a dn or a username. If both a dn and
        a username is provided, the dn will be used.

        Args:
            - dn -- The full Distinguished Name of a user.
            - id -- The user ID of the user to return.

        Returns:
            The User object if one could be created, otherwise None
        """
        if dn is not None:
            try:
                user = cls(dn=dn)
                user.id = user.ion_id
                return user
            except (ldap.INVALID_DN_SYNTAX, ldap.NO_SUCH_OBJECT):
                return None

        elif id is not None:
            user_dn = User.dn_from_id(id)
            if user_dn is not None:
                return cls(dn=user_dn, id=id)
            else:
                return None
        else:
            return None

    @classmethod
    def dn_from_id(cls, id):
        c = LDAPConnection()
        result = c.search(settings.USER_DN, "(&(|(objectClass=tjhsstStudent)(objectClass=tjhsstTeacher))(iodineUidNumber={}))".format(id), ['dn'])
        if len(result) == 1:
            return result[0][0]
        else:
            return None

    @staticmethod
    def create_secure_cache_key(identifier):
        """Create a cache key for sensitive information.

        Caching personal information that was once access-protected
        introduces an inherent security risk. To prevent human retrieval
        of a value from the cache, the plaintext key is first signed
        with the secret key and then hashed using the SHA1 algorithm.
        That way, one would need the secret key to query for a specifi
        cached value and an existing key would indicate nothing about
        the relevance of the cooresponding value. For maximum
        effectiveness, cache attributes of an object separately so the
        context of a cached value can not be inferred (e.g. cache a
        user's name separate from his or her address so the two can not
        be associated).

        Args:
            identifier: The plaintext identifier (generally of the form\
                        "<dn>.<attribute>" for the cached data).

        Returns:
            String

        """
        signer = Signer()
        signed = signer.sign(identifier)
        hash = hashlib.sha1()
        hash.update(signed)
        return hash.hexdigest()

    def get_full_name(self):
        """Return full name, e.g. Angela William. This is required
        for subclasses of User."""
        return self.cn

    full_name = property(get_full_name)

    def get_short_name(self):
        """Return short name (first name) of a user. This is required
        for subclasses of User.
        """
        return self.first_name

    short_name = property(get_short_name)

    def get_dn(self):
        """Return the full distinguished name for a user in LDAP."""
        return "iodineUid=" + self.username + "," + settings.USER_DN

    def set_dn(self, dn):
        """Set DN for a user and use the DN to populate the
        username field.
        """
        self.username = ldap.dn.str2dn(dn)[0][0][1]

    dn = property(get_dn, set_dn)

    def get_classes(self):
        """Returns a list of Class objects for a user ordered by
        period number.

        Returns:
            List of Class objects

        """
        identifier = ".".join([self.dn, "classes"])
        key = User.create_secure_cache_key(identifier)

        cached = cache.get(key)
        visible = self.attribute_is_visible("showschedule")

        if cached and visible:
            logger.debug("Attribute 'classes' of user {} loaded \
                          from cache.".format(self.username))
            schedule = []
            for dn in cached:
                class_object = Class(dn=dn)
                schedule.append(class_object)
            return schedule
        elif not cached and visible:
            c = LDAPConnection()
            try:
                results = c.user_attributes(self.dn, ['enrolledclass'])
                classes = results.first_result()["enrolledclass"]
                schedule = []
                for dn in classes:
                    class_object = Class(dn=dn)

                    # Temporarily pack the classes in tuples so we can
                    # sort on an integer key instead of the period
                    # property to avoid tons of needless LDAP queries
                    schedule.append((class_object.period, class_object, dn))

                ordered_schedule = sorted(schedule, key=lambda e: e[0])

                # Prepare a list of DNs for caching
                # (pickling a Class class loads all properties
                # recursively and quickly reaches the maximum
                # recursion depth)
                dn_list = list(zip(*ordered_schedule)[2])
                cache.set(key, dn_list, settings.USER_CLASSES_CACHE_AGE)
                return list(zip(*ordered_schedule)[1])  # Unpacked class list
            except KeyError:
                return None
        else:
            return None

    classes = property(get_classes)

    # TODO:
    # counselor
    # homephone
    # gender
    # email

    def get_address(self):
        """Returns the address of a user.

        Returns:
            Address object

        """
        identifier = ".".join([self.dn, "address"])
        key = User.create_secure_cache_key(identifier)

        cached = cache.get(key)
        visible = self.attribute_is_visible("showaddress")

        if cached and visible:
            logger.debug("Attribute 'address' of user {} loaded \
                          from cache.".format(self.username))
            return cached
        elif not cached and visible:
            c = LDAPConnection()
            try:
                raw = c.user_attributes(self.dn,
                                        ['street', 'l', 'st', 'postalCode'])
                result = raw.first_result()
                street = result['street'][0]
                city = result['l'][0]
                state = result['st'][0]
                postal_code = result['postalCode'][0]

                address_object = Address(street, city, state, postal_code)
                cache.set(key, address_object,
                          settings.USER_ATTRIBUTE_CACHE_AGE)
                return address_object
            except KeyError:
                return None
        else:
            return None
    address = property(get_address)

    def get_birthday(self):
        """Returns a user's birthday.

        Returns:
            datetime object

        """
        identifier = ".".join([self.dn, "birthday"])
        key = User.create_secure_cache_key(identifier)

        cached = cache.get(key)
        visible = self.attribute_is_visible("showbirthday")

        if cached and visible:
            logger.debug("Attribute 'birthday' of user {} loaded \
                          from cache.".format(self.username))
            return cached
        elif not cached and visible:
            c = LDAPConnection()
            try:
                result = c.user_attributes(self.dn, ["birthday"])
                birthday = result.first_result()["birthday"][0]
                date_object = datetime.datetime.strptime(birthday, '%Y%m%d')
                cache.set(key, date_object, settings.USER_ATTRIBUTE_CACHE_AGE)
                return date_object
            except KeyError:
                return None
        else:
            return None

    birthday = property(get_birthday)

    def get_permissions(self):
        """Fetches the LDAP permissions for a user.

        Returns:
            Dictionary with keys "parent" and "self", each mapping to a
            list of permissions.
        """
        key = ".".join([self.dn, 'user_info_permissions'])

        cached = cache.get(key)

        if cached:
            logger.debug("Permissions of user {} loaded \
                          from cache.".format(self.username))
            return cached
        else:
            c = LDAPConnection()
            raw = c.user_attributes(self.dn, ["perm-showaddress",
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
                                              "perm-showpictures-self",
                                              ])
            results = raw.first_result()
            perms = {"parent": {}, "self": {}}
            for perm, value in results.iteritems():
                bool_value = True if (value[0] == 'TRUE') else False
                if perm.endswith("-self"):
                    perm_name = perm[5:-5]
                    perms["self"][perm_name] = bool_value
                else:
                    perm_name = perm[5:]
                    perms["parent"][perm_name] = bool_value

            cache.set(key, perms, settings.LDAP_PERMISSIONS_CACHE_AGE)
            return perms

    permissions = property(get_permissions)

    def attribute_is_visible(self, ldap_perm_name):
        perms = self.permissions

        try:
            own_info = threadlocals.current_user().id == self.id
        except AttributeError:
            own_info = False

        public = True
        if ldap_perm_name in perms["parent"]:
            public = perms["parent"][ldap_perm_name]
        if ldap_perm_name in perms["self"]:
            public = public and perms["self"][ldap_perm_name]

        return own_info or public

    def __getattr__(self, name):
        """Return simple attributes of User

        This is used to retrieve ldap fields that don't require special
        processing, e.g. email or graduation year. Fields names are
        mapped to more user friendly names to increase readability of
        templates. When more complex processing is required or a
        complex return type is required, (such as a datetime object for
        a birthday), properties should be used instead.

        Note that __getattr__ is used instead of __getattribute__ so
        the method is called after checking regular attributes instead
        of before.

        Returns:
            Either a list of strings or a string, depending on
            the attribute fetched.

        """
        identifier = ".".join([self.dn, name])
        key = User.create_secure_cache_key(identifier)

        cached = cache.get(key)

        attr_ldap_field_map = {"ion_id": ("iodineUidNumber", False),
                               "cn": ("cn", False),
                               "display_name": ("displayName", False),
                               "title": ("title", False),
                               "first_name": ("givenName", False),
                               "middle_name": ("middlename", False),
                               "last_name": ("sn", False),
                               "object_class": ("objectClass", False),
                               "locker": ("locker", True),
                               "graduation_year": ("graduationYear", False),
                               "home_phone": ("homePhone", 'showtelephone'),
                               "mobile_phone": ("mobile", False),
                               "other_phones": ("telephoneNumber", False),
                               "google_talk": ("googleTalk", False),
                               "skype": ("skype", False),
                               "webpage": ("webpage", False),
                               }

        ldap_field = attr_ldap_field_map[name]

        if ldap_field[1] is False:
            visible = True
        else:
            visible = self.attribute_is_visible(ldap_field[1])

        if cached and visible:
            logger.debug("Attribute '{}' of user {} loaded \
                          from cache.".format(name, self.username))
            return cached
        elif not cached and visible:
            # This map essentially turns camelcase names into
            # Python-style attribute names. The second  elements of
            # the tuples indicateds whether the piece of information
            # is restricted in LDAP (false if not protected, else the
            # name of the permission)

            if name in attr_ldap_field_map:
                c = LDAPConnection()
                field_name = ldap_field[0]
                try:
                    result = c.user_attributes(self.dn, [field_name])
                    fields = result.first_result()
                    value = fields[field_name][0]
                    cache.set(key, value, settings.USER_ATTRIBUTE_CACHE_AGE)
                    return value
                except KeyError:
                    return None
            else:
                # Default behaviour
                logger.debug("Attribute {} of user not found.".format(name))
                raise AttributeError
        else:
            return None


class Class(object):
    """Represents a tjhsstClass LDAP object.

    Attributes:
        - dn -- The DN of the cooresponding tjhsstClass in LDAP
        - section_id -- The section ID of the class

    """
    def __init__(self, dn):
        """Initialize the Class object."""
        self.dn = dn

    section_id = property(lambda c: ldap.dn.str2dn(c.dn)[0][0][1])

    def get_teacher(self):
        """Returns the teacher/sponsor of the class

        Returns:
            User object

        """
        key = ".".join([self.dn, 'teacher'])

        cached = cache.get(key)

        if cached:
            logger.debug("Attribute 'teacher' of class {} loaded \
                          from cache.".format(self.section_id))
            return User.create(dn=cached)
        else:
            c = LDAPConnection()
            results = c.class_attributes(self.dn, ['sponsorDn'])
            result = results.first_result()
            dn = result['sponsorDn'][0]

            # Only cache the dn, since pickling would recursively fetch
            # all of the properties and quickly reach the maximum
            # recursion depth
            cache.set(key, dn, settings.CLASS_TEACHER_CACHE_AGE)
            return User.create(dn=dn)

    teacher = property(get_teacher)

    # TODO:
    # quarters

    def __getattr__(self, name):
        """Return simple attributes of User

        This is used to retrieve ldap fields that don't require special
        processing, e.g. roomNumber or period. Fields names are
        mapped to more user friendly names to increase readability of
        templates. When more complex processing is required or a
        complex return type is required, (such as a User object),
        properties should be used instead.

        Note that __getattr__ is used instead of __getattribute__ so
        the method is called after checking regular attributes instead
        of before.

        Returns:
            Either a list of strings or a string, depending on \
            the attribute fetched.


        """
        key = ".".join([self.dn, name])

        cached = cache.get(key)

        if cached:
            logger.debug("Attribute '{}' of class {} loaded \
                          from cache.".format(name, self.section_id))
            return cached
        else:
            attr_ldap_field_map = {"name": "cn",
                                   "period": "classPeriod",
                                   "class_id": "tjhsstClassId",
                                   "course_length": "courseLength",
                                   "room_number": "roomNumber",
                                   }

            if name in attr_ldap_field_map:
                c = LDAPConnection()
                field_name = attr_ldap_field_map[name]
                try:
                    result = c.class_attributes(self.dn, [field_name])
                    fields = result.first_result()
                    value = fields[field_name][0]
                    cache.set(key, value, settings.CLASS_ATTRIBUTE_CACHE_AGE)
                    return value
                except KeyError:
                    return None
            else:
                # Default behaviour
                raise AttributeError


class Address(object):
    """Represents the address of a user.

    Attributes:
        - street -- The street name of the address.
        - city -- The city name of the address.
        - state -- The state name of the address.
        - postal_code -- The zip code of the address.

    """
    def __init__(self, street, city, state, postal_code):
        """Initialize the Address object."""
        self.street = street
        self.city = city
        self.state = state
        self.postal_code = postal_code

    def __unicode__(self):
        """Return unicode representation for debugging."""
        return "{}; {}, {} {}".format(self.street, self.city, self.state,
                                      self.postal_code)
