import logging
import datetime
import ldap
from intranet.db.ldap_db import LDAPConnection
from intranet import settings
from django.db import models
from django.contrib.auth.models import AbstractBaseUser

logger = logging.getLogger(__name__)


class UserManager(models.Manager):
    def return_something(self):
        return "something"


class User(AbstractBaseUser):
    username = models.CharField(max_length=50, unique=True, db_index=True)
    # first_name = models.CharField(max_length=50)
    # last_name = models.CharField(max_length=50)

    USERNAME_FIELD = 'username'
    objects = UserManager()

    def get_full_name(self):
        if self.display_name:
            return self.display_name
        else:
            return self.cn
    full_name = property(get_full_name)

    def get_short_name(self):
        return self.first_name
    short_name = property(get_short_name)

    def get_dn(self):
        return "iodineUid=" + self.username + "," + settings.USER_DN
    def set_dn(self, dn):
        self.username = ldap.dn.str2dn(dn)[0][0][1]
    dn = property(get_dn, set_dn)

    # Return ordered schedule
    def get_classes(self):
        c = LDAPConnection()
        try:
            result = c.user_attributes(self.dn, ['enrolledclass'])
            classes = result.first_result()["enrolledclass"]
            schedule = []
            for dn in classes:
                class_object = Class(dn=dn)
                schedule.append(class_object)
            return sorted(schedule, key=lambda e: e.period)
        except KeyError:
            return None
    classes = property(get_classes)

    # TODO:
    # counselor
    # homephone
    # address
    # gender
    # email

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

    # Using __getattr__ instead of __getattribute__ so it is called after checking regular attributes
    def __getattr__(self, name):
        # Maps simple attributes of User to ldap fields
        # When more complex processing is required (such as when a date object is returned), a property is used instead
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

    # Using __getattr__ instead of __getattribute__ so it is called after checking regular attributes
    def __getattr__(self, name):
        # Maps simple attributes of User to ldap fields
        # When more complex processing is required (such as when a date object is returned), a property is used instead
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
