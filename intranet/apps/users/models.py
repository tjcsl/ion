import logging
import ldap
import hashlib
from datetime import datetime
from django.db import models
from django import template
from django.core.cache import cache
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.core.signing import Signer
from intranet.db.ldap_db import LDAPConnection
from intranet import settings
from intranet.middleware import threadlocals

logger = logging.getLogger(__name__)
register = template.Library()


class UserManager(UserManager):

    """User model Manager for table-level LDAP queries.

    Provides table-level LDAP abstraction for the User model. If a call
    to a method fails for this Manager, the call is deferred to the
    default User model manager.

    """
    pass


class User(AbstractBaseUser, PermissionsMixin):

    """Django User model subclass with properties that fetch data
    from LDAP

    Represents a tjhsstStudent or tjhsstTeacher LDAP object.Extends
    AbstractBaseUser so the model will work with Django's built-in
    authorization functionality.

    The User model is primarily an abstraction of LDAP which has just
    enough fields duplicated in the SQL database for Django to accept
    it as a valid user model that can have relations to other models in
    the database.

    When creating a user object, use User.get_user() so the User object
    can access all of its data in LDAP. Using the default User()
    constructor is not a good idea, since, for example, if you create a
    user object form a DN (User(dn="...'')), you will not be able to
    fetch the user id.

    When fetching a username, do not use the username attribute.
    Instead, use ion_username, which pulls the username from LDAP
    instead of the SQL database, which does not necessarily contain the
    user object.

    """

    # Django Model Fields
    username = models.CharField(max_length=30, unique=True)

    # Private dn cache
    _dn = None

    # Required to replace the default Django User model
    USERNAME_FIELD = "username"

    """Override default Model Manager (objects) with
    custom UserManager to add table-level functionality."""
    objects = UserManager()

    @classmethod
    def get_user(cls, dn=None, id=None, username=None):
        """Retrieve a user object from LDAP

        Creates a User object from a dn, user id, or a username based on
        data in the LDAP database.

        Args:
            - dn -- The full LDAP Distinguished Name of a user.
            - id -- The user ID of the user to return.
            - username -- The username of the user to return.

        Returns:
            The User object if the user could be found in LDAP,
            otherwise None
        """
        if dn is not None:
            try:
                user = User(dn=dn)
                user.id = user.ion_id

                return user
            except (ldap.INVALID_DN_SYNTAX, ldap.NO_SUCH_OBJECT):
                return None
        elif id is not None:
            user_dn = User.dn_from_id(id)
            if user_dn is not None:
                return User(dn=user_dn, id=id)
            else:
                return None
        elif username is not None:
            dn = User.dn_from_username(username)
            return get_user(dn=dn)
        else:
            return None

    @classmethod
    def dn_from_id(cls, id):
        """Get a dn, given an ID.

        Args:
            - id -- the ID of the user.

        Returns:
            - String if dn was found, otherwise None

        """
        key = ":".join([str(id), 'dn'])
        cached = cache.get(key)

        if cached:
            logger.debug("DN for User with ID {} loaded "
                         "from cache.".format(id))
            return cached
        else:
            c = LDAPConnection()
            result = c.search(settings.USER_DN,
                              "(&(|(objectClass=tjhsstStudent)"
                              "(objectClass=tjhsstTeacher))"
                              "(iodineUidNumber={}))".format(id),
                              ['dn'])
            if len(result) == 1:
                dn = result[0][0]
            else:
                dn = None
            cache.set(key, dn, timeout=settings.CACHE_AGE['dn_id_mapping'])
            return dn

    @classmethod
    def dn_from_username(cls, username):
        return "iodineUid=" + username + "," + settings.USER_DN

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
            - identifier -- The plaintext identifier (generally of the \
                            form "<dn>.<attribute>" for the cached data).

        Returns:
            String

        """
        signer = Signer()
        signed = signer.sign(identifier)
        hash = hashlib.sha1()
        hash.update(signed)
        return hash.hexdigest()

    @property
    def full_name(self):
        """Return full name, e.g. Angela William. This is required
        for subclasses of User."""
        return self.cn

    @property
    def short_name(self):
        """Return short name (first name) of a user. This is required
        for subclasses of User.
        """
        return self.first_name

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
        identifier = ":".join([self.dn, "classes"])
        key = User.create_secure_cache_key(identifier)

        cached = cache.get(key)
        visible = self.attribute_is_visible("showschedule")

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
                results = c.user_attributes(self.dn, ['enrolledclass'])
                classes = results.first_result()["enrolledclass"]
            except KeyError:
                return None
            else:
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
                cache.set(key, dn_list,
                          timeout=settings.CACHE_AGE['user_classes'])
                return list(zip(*ordered_schedule)[1])  # Unpacked class list
        else:
            return None

    # TODO: gender
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

    def photo_binary(self, photo_year):
        """Returns the binary data for a user's picture.

        Returns:
            Binary data

        """
        identifier = ":".join([self.dn, "photo", photo_year])
        key = identifier  # User.create_secure_cache_key(identifier)

        cached = cache.get(key)

        if self.own_info():
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
                perms["self"]["default"] = \
                    (default["perm-showpictures-self"][0] == "TRUE")

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
                      timeout=settings.CACHE_AGE['ldap_permissions'])
            return perms

    @property
    def permissions(self):
        """Fetches the LDAP permissions for a user.

        Returns:
            Dictionary with keys "parent" and "self", each mapping to a
            list of permissions.
        """
        key = ":".join([self.dn, 'user_info_permissions'])

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
                                                  "perm-showaddress-self",
                                                  "perm-showtelephone-self",
                                                  "perm-showbirthday-self",
                                                  "perm-showschedule-self",
                                                  "perm-showeighth-self",
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
    def is_staff(self):
        """Checks if a user is a tjhsstTeacher.

        Returns:
            Boolean

        """
        return self.user_type == "tjhsstTeacher"

    def own_info(self):
        """Checks if a user is viewing his or her own info.

        Used primarily to load private personal information from the
        cache. (A student should see all info on his or her own profile
        regardless of how the permissions are set.)

        Returns:
            Boolean

        """
        try:
            return (str(threadlocals.request().user.id) == str(self.id))
        except AttributeError:
            return False

    def attribute_is_visible(self, ldap_perm_name):
        """Checks if an attribute is visible to the public.

        Args:
            - ldap_perm_name -- the name of the permission to check.

        Returns:
            Boolean

        """
        perms = self.permissions

        if self.own_info():
            return True
        else:
            public = True
            if ldap_perm_name in perms["parent"]:
                public = perms["parent"][ldap_perm_name]
            if ldap_perm_name in perms["self"]:
                public = public and perms["self"][ldap_perm_name]
            return public

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
        identifier = ":".join([self.dn, name])
        key = User.create_secure_cache_key(identifier)

        cached = cache.get(key)

        # This map essentially turns camelcase names into
        # Python-style attribute names. The second  elements of
        # the tuples indicateds whether the piece of information
        # is restricted in LDAP (false if not protected, else the
        # name of the permission).
        user_attributes = {
            "ion_id": {
                "ldap_name": "iodineUidNumber",
                "perm": None,
                "list": False
            },
            "ion_username": {
                "ldap_name": "iodineUid",
                "perm": None,
                "list": False
            },
            "cn": {
                "ldap_name": "cn",
                "perm": None,
                "list": False
            },
            "display_name": {
                "ldap_name": "displayName",
                "perm": None,
                "list": False
            },
            "title": {
                "ldap_name": "title",
                "perm": None,
                "list": False
            },
            "first_name": {
                "ldap_name": "givenName",
                "perm": None,
                "list": False
            },
            "middle_name": {
                "ldap_name": "middlename",
                "perm": None,
                "list": False
            },
            "last_name": {
                "ldap_name": "sn",
                "perm": None,
                "list": False
            },
            "user_type": {
                "ldap_name": "objectClass",
                "perm": None,
                "list": False
            },
            "graduation_year": {
                "ldap_name": "graduationYear",
                "perm": None,
                "list": False
            },
            "preferred_photo": {
                "ldap_name": "preferredPhoto",
                "perm": None,
                "list": False
            },
            "emails": {
                "ldap_name": "mail",
                "perm": None,
                "list": True
            },
            "home_phone": {
                "ldap_name": "homePhone",
                "perm": "showtelephone",
                "list": False
            },
            "mobile_phone": {
                "ldap_name": "mobile",
                "perm": None,
                "list": False
            },
            "other_phones": {
                "ldap_name": "telephoneNumber",
                "perm": None,
                "list": True
            },
            "google_talk": {
                "ldap_name": "googleTalk",
                "perm": None,
                "list": False
            },
            "skype": {
                "ldap_name": "skype",
                "perm": None,
                "list": False
            },
            "webpages": {
                "ldap_name": "webpage",
                "perm": None,
                "list": True
            },
        }

        if name in user_attributes:
            attr = user_attributes[name]
        else:
            raise AttributeError

        if attr["perm"] is None:
            visible = True
        else:
            visible = self.attribute_is_visible(attr["perm"])

        if cached and visible:
            logger.debug("Attribute '{}' of user {} loaded "
                         "from cache.".format(name, self.id))
            return cached
        elif not cached and visible:
            if name in user_attributes:
                c = LDAPConnection()
                field_name = attr["ldap_name"]
                try:
                    results = c.user_attributes(self.dn, [field_name])
                    result = results.first_result()[field_name]

                    if attr["list"]:
                        value = result
                    else:
                        value = result[0]

                    cache.set(key, value,
                              timeout=settings.CACHE_AGE["user_attribute"])
                    return value
                except KeyError:
                    return None
            else:
                logger.debug("Attribute {} of user not found.".format(name))
                raise AttributeError
        else:
            return None

    def __unicode__(self):
        return self.username or self.ion_username or self.id


class Class(object):

    """Represents a tjhsstClass LDAP object.

    Attributes:
        - dn -- The DN of the cooresponding tjhsstClass in LDAP
        - section_id -- The section ID of the class

    """

    def __init__(self, dn):
        """Initialize the Class object.

        Args:
            - dn -- The full DN of the class.

        """
        self.dn = dn

    section_id = property(lambda c: ldap.dn.str2dn(c.dn)[0][0][1])

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

        This method should not be called manually - use dot notation or
        getattr() to fetch an attribute.

        Args:
            - name -- The string name of the attribute.

        Returns:
            Either a list of strings or a string, depending on \
            the attribute fetched.


        """
        key = ":".join([self.dn, name])

        cached = cache.get(key)

        if cached:
            logger.debug("Attribute '{}' of class {} loaded "
                         "from cache.".format(name, self.section_id))
            return cached
        else:
            class_attributes = {
                "name": {
                    "ldap_name": "cn",
                    "list": False
                },
                "period": {
                    "ldap_name": "classPeriod",
                    "list": False
                },
                "class_id": {
                    "ldap_name": "tjhsstClassId",
                    "list": False
                },
                "course_length": {
                    "ldap_name": "courseLength",
                    "list": False
                },
                "room_number": {
                    "ldap_name": "roomNumber",
                    "list": False
                }
            }

            if name in class_attributes:
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
                    if attr["list"]:
                        value = result
                    else:
                        value = result[0]

                    cache.set(key, value,
                              timeout=settings.CACHE_AGE['class_attribute'])
                    return value
            else:
                # Default behaviour
                raise AttributeError


class Address(object):

    """Represents a user's address.

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
        """Returns full address string."""
        return "{}\n{}, {} {}".format(self.street, self.city,
                                      self.state, self.postal_code)


class Grade(object):

    """Represents a user's grade."""
    names = ["freshman", "sophomore", "junior", "senior", "graduate"]

    def __init__(self, graduation_year):
        """Initialize the Grade object.

        Args:
            - graduation_year -- The graduation year of the user (e.g. 1492)
        """
        self._year = int(graduation_year)
        today = datetime.now()
        if today.month >= 7:
            current_senior_year = today.year + 1
        else:
            current_senior_year = today.year

        self._number = current_senior_year - self._year + 12

        if self._number in range(9, 14):
            self._name = Grade.names[self._number - 9]
        else:
            self._name = None

    def number(self):
        """Return the grade as a number (9-12).

        For use in templates since there is no nice integer conversion.
        In Python code, use int() on a Grade object instead.

        """
        return self._number

    def __int__(self):
        """Return the grade as a number (9-12)."""
        return self._number

    def __unicode__(self):
        """Return name of the grade."""
        return self._name
