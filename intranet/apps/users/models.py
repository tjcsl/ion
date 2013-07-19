import logging
import datetime
import ldap
from intranet.db.ldap_db import LDAPConnection
from intranet import settings
from django.db import models
from django.contrib.auth.models import AbstractBaseUser

logger = logging.getLogger(__name__)


class UserManager(models.Manager):
    """User model Manager for table-level LDAP queries.

    Provides table-level LDAP abstraction for the User model. If a call
    to a method fails for this Manager, the call is deferred to the
    default User model manager.

    """
    def return_something(self):
        return "something"


class User(AbstractBaseUser):
    """User model with properties that fetch data from LDAP

    Extends AbstractBaseUser so the model will work with Django's
    built-in authorization functionality.

    """
    # Django Model Fields
    username = models.CharField(max_length=50, unique=True, db_index=True)
    # first_name = models.CharField(max_length=50)
    # last_name = models.CharField(max_length=50)

    """Required to replace the default User model."""
    USERNAME_FIELD = 'username'

    """Override default Model Manager (objects) with
    custom UserManager."""
    objects = UserManager()

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
        """Return short name (first name) of a user."""
        return self.first_name

    short_name = property(get_short_name)

    def get_dn(self):
        """Return the full distinguished name for a user in LDAP."""
        return "iodineUid=" + self.username + "," + settings.USER_DN

    def set_dn(self, dn):
        """Set DN for a user.
        This should only be used for constructing ad-hoc User objects.

            >>> User(dn="iodineUid=awilliam,ou=people,dc=tjhsst,dc=edu")

        """
        self.username = ldap.dn.str2dn(dn)[0][0][1]

    dn = property(get_dn, set_dn)

    def get_classes(self):
        """Returns a list of Class objects for a user ordered by
        period number.
        """
        c = LDAPConnection()
        try:
            result = c.user_attributes(self.dn, ['enrolledclass'])
            classes = result.first_result()["enrolledclass"]
            schedule = []

            for dn in classes:
                class_object = Class(dn=dn)

                # Temporarily pack the classes in tuples so we can
                # sort on an integer key instead of the period property
                # to avoid tons of needless LDAP queries
                schedule.append((class_object.period, class_object))

            ordered_schedule = sorted(schedule, key=lambda e: e[0])
            return list(zip(*ordered_schedule)[1])
        except KeyError:
            return None
    classes = property(get_classes)

    # TODO:
    # counselor
    # homephone
    # address
    # gender
    # email

    def get_address(self):
        c = LDAPConnection()
        try:
            raw = c.user_attribues(self.dn, 
                                   ['street', 'postalCode', 'st', 'l'])
            result = raw.first_result()
            street = result['street'][0]
            postalCode = result['postalCode'][0]
            st = result['st'][0]
            l = result['l'][0]
        except KeyError:
            return None
        address_object = Address(street, postalCode, st, l)
        return address_object
    address = property(get_address)

    def get_birthday(self):
        c = LDAPConnection()
        try:
            result = c.user_attributes(self.dn, ["birthday"])
            birthday = result.first_result()["birthday"][0]
            date_object = datetime.datetime.strptime(birthday, '%Y%m%d')
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
            the input.


        """
        attr_ldap_field_map = {"home_phone": "homePhone",
                               "email": "mail",
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
                return fields[field_name][0]
            except KeyError:
                return None
        else:
            # Default behaviour
            raise AttributeError


class Class(object):
    def __init__(self, dn):
        self.dn = dn

    section_id = property(lambda c: ldap.dn.str2dn(c.dn)[0][0][1])

    def get_sponsor(self):
        c = LDAPConnection()
        result = c.class_attributes(self.dn, ['sponsorDn']).first_result()
        return User(dn=result['sponsorDn'][0])
    teacher = property(get_sponsor)

    def __getattr__(self, name):
        attr_ldap_field_map = {"name": "cn",
                               "period": "classPeriod",
                               "class_id": "tjhsstClassId",
                               # "section_id": "tjhsstSectionId",
                               "course_length": "courseLength",
                               # "quarters": "quarterNumber",
                               "room_number": "roomNumber",
                               }

        if name in attr_ldap_field_map:
            c = LDAPConnection()
            field_name = attr_ldap_field_map[name]
            try:
                result = c.class_attributes(self.dn, [field_name])
                fields = result.first_result()
                return fields[field_name][0]
            except KeyError:
                return None
        else:
            # Default behaviour
            raise AttributeError

class Address(object):
    def __init__(self, street, l, st, postalCode):
        self.street = street
        self.l = l
        self.st = st
        self.postalCode = postalCode

    def __unicode__(self):
        return ', '.join(self.street, self.l, self.st, self.postalCode)
