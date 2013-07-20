import logging
import datetime
import ldap
import hashlib
from intranet.db.ldap_db import LDAPConnection
from intranet import settings
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

    @staticmethod
    def create_secure_cache_key(identifier):
        """Create a cache key for sensitive information.

        Caching personal information that was once access-protected
        introduces an inherent security risk. To prevent retrieval of a
        value from the cache, the plaintext key is first signed with the
        secret key and then hashed using the SHA1 algorithm. That way,
        one would need the secret key to construct the key for a
        cached value and an existing key indicates nothing about the
        relevance of the cooresponding value. For maximum effectiveness,
        cache attributes of an object separately so the relevance of
        cached info can not be inferred (e.g. cache a user's name
        separate from his or her address so the two can not be
        associated).

        Args:
            identifier: The plaintext identifier (generally of the form
                "<dn>.<attribute>" for the cached data.

        Returns:
            String

        """
        signer = Signer()
        signed = signer.sign(identifier)
        hash = hashlib.sha1()
        hash.update(signed)
        return hash.hexdigest()

    def get_full_name(self):
        """Return full name, e.g. Guido van Rossum or Angela William,
        depending on what information is available in LDAP.
        """
        if self.display_name:
            return self.display_name
        else:
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
        """Set DN for a user. This should generally only be used for
        constructing ad-hoc User objects.

            >>> User(dn="iodineUid=awilliam,ou=people,dc=tjhsst,dc=edu")

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

        if cached:
            logger.debug("Attribute 'classes' of user {} loaded \
                          from cache.".format(self.username))
            schedule = []
            for dn in cached:
                class_object = Class(dn=dn)
                schedule.append(class_object)
            return schedule
        else:
            c = LDAPConnection()
            try:
                results = c.user_attributes(self.dn, ['enrolledclass'])
                classes = results.first_result()["enrolledclass"]
                schedule = []
                dn_list = []
                for dn in classes:
                    class_object = Class(dn=dn)

                    # Prepare a list of DNs for caching
                    # (pickling a Class class loads all properties recursively
                    # and quickly reaches the maximum recursion depth)
                    dn_list.append(dn)

                    # Temporarily pack the classes in tuples so we can
                    # sort on an integer key instead of the period property
                    # to avoid tons of needless LDAP queries
                    schedule.append((class_object.period, class_object))

                cache.set(key, dn_list,
                          settings.USER_CLASSES_CACHE_AGE)

                ordered_schedule = sorted(schedule, key=lambda e: e[0])
                return list(zip(*ordered_schedule)[1])  # Unpacked class list
            except KeyError:
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

        if cached:
            logger.debug("Attribute 'address' of user {} loaded \
                          from cache.".format(self.username))
            return cached
        else:
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
    address = property(get_address)

    def get_birthday(self):
        """Returns a user's birthday.

        Returns:
            datetime object

        """
        identifier = ".".join([self.dn, "birthday"])
        key = User.create_secure_cache_key(identifier)

        cached = cache.get(key)

        if cached:
            logger.debug("Attribute 'birthday' of user {} loaded \
                          from cache.".format(self.username))
            return cached
        else:
            c = LDAPConnection()
            try:
                result = c.user_attributes(self.dn, ["birthday"])
                birthday = result.first_result()["birthday"][0]
                date_object = datetime.datetime.strptime(birthday, '%Y%m%d')
                cache.set(key, date_object, settings.USER_ATTRIBUTE_CACHE_AGE)
                return date_object
            except KeyError:
                return None

    birthday = property(get_birthday)

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

        if cached:
            logger.debug("Attribute '{}' of user {} loaded \
                          from cache.".format(name, self.username))
            return cached
        else:
            attr_ldap_field_map = {"home_phone": "homePhone",
                                   "ion_id": "iodineUidNumber",
                                   "student_id": "tjhsstStudentId",
                                   "first_name": "givenName",
                                   "middle_name": "middlename",
                                   "last_name": "sn",
                                   "locker": "locker",
                                   "graduation_year": "graduationYear",
                                   "display_name": "displayName",
                                   "cn": "cn",
                                   "title": "title",
                                   }

            if name in attr_ldap_field_map:
                c = LDAPConnection()
                field_name = attr_ldap_field_map[name]
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


class Class(object):
    """Represents a tjhsstClass LDAP object.

    Attributes:
        dn: The DN of the cooresponding tjhsstClass in LDAP
        section_id: The section ID of the class

    """
    def __init__(self, dn):
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
            return User(dn=cached)
        else:
            c = LDAPConnection()
            results = c.class_attributes(self.dn, ['sponsorDn'])
            result = results.first_result()
            dn = result['sponsorDn'][0]

            # Only cache the dn, since pickling would recursively fetch
            # all of the properties and quickly reach the maximum
            # recursion depth
            cache.set(key, dn, settings.CLASS_TEACHER_CACHE_AGE)
            return User(dn=dn)
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
            Either a list of strings or a string, depending on
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
        street: The street name of the address.
        city: The city name of the address.
        state: The state name of the address.
        postal_code: The zip code of the address.

    """
    def __init__(self, street, city, state, postal_code):
        self.street = street
        self.city = city
        self.state = state
        self.postal_code = postal_code

    def __unicode__(self):
        return "{}; {}, {} {}".format(self.street, self.city, self.state,
                                      self.postal_code)
