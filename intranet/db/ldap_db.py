# -*- coding: utf-8 -*-

import logging
import sys
from threading import local

from django.conf import settings
from django.core.handlers.wsgi import WSGIHandler
from django.core.signals import request_finished
from django.dispatch import receiver

try:
    import gssapi
except ImportError:
    pass

import ldap3
import ldap3.protocol.sasl
import ldap3.utils.conv

logger = logging.getLogger(__name__)
_thread_locals = local()


class LDAPFilter(object):

    @staticmethod
    def operator(operator, *conditions):
        return "(" + operator + "".join(("(" + c + ")" for c in conditions)) + ")"

    @staticmethod
    def and_filter(*conditions):
        return LDAPFilter.operator("&", *conditions)

    @staticmethod
    def or_filter(*conditions):
        return LDAPFilter.operator("|", *conditions)

    @staticmethod
    def escape(text):
        return ldap3.utils.conv.escape_filter_chars(text)

    @staticmethod
    def attribute_in_list(attribute, values):
        """Returns a filter for selecting all entries for which a specified attribute is contained
        in a specified list of values."""
        conditions = (attribute + "=" + v for v in values)
        return LDAPFilter.or_filter(*conditions)

    @staticmethod
    def all_users():
        """Returns a filter for selecting all user objects in LDAP."""

        user_object_classes = sorted(list(settings.LDAP_OBJECT_CLASSES.values()))
        return LDAPFilter.attribute_in_list("objectclass", user_object_classes)


class LDAPConnection(object):
    """Represents an LDAP connection with wrappers for the raw ldap queries.

    Attributes:
        conn
            The singleton LDAP connection.

    """

    def simple_bind(self, server):
        _thread_locals.ldap_conn = ldap3.Connection(server, settings.AUTHUSER_DN, settings.AUTHUSER_PASSWORD)
        try:
            _thread_locals.ldap_conn.bind()
        except ldap3.LDAPSocketOpenError as e:
            logging.critical("Failed to connect to ldap server: %s", e)
            _thread_locals.ldap_conn = None
        _thread_locals.simple_bind = True

    @property
    def conn(self):
        """Lazily load and return the raw connection from threadlocals.

        Connect to the LDAP server specified in settings and bind using
        the GSSAPI protocol. The requisite KRB5CCNAME environmental
        variable should have already been set by the SetKerberosCache
        middleware.

        """
        ldap_exceptions = (ldap3.LDAPExceptionError, ldap3.LDAPSocketOpenError)
        if 'gssapi' in sys.modules:
            ldap_exceptions += (gssapi.exceptions.GSSError,)

        if not hasattr(_thread_locals, "ldap_conn") or _thread_locals.ldap_conn is None:
            logger.info("Connecting to LDAP...")
            server = ldap3.Server(settings.LDAP_SERVER)
            if settings.USE_SASL:
                try:
                    _thread_locals.ldap_conn = ldap3.Connection(server, authentication=ldap3.SASL, sasl_mechanism='GSSAPI')
                    _thread_locals.ldap_conn.bind()
                    _thread_locals.simple_bind = False
                    logger.info("Successfully connected to LDAP.")
                except ldap_exceptions as e:
                    logger.warning("SASL bind failed - using simple bind")
                    logger.warning(e)
                    self.simple_bind(server)
            else:
                self.simple_bind(server)

        return _thread_locals.ldap_conn

    def did_use_simple_bind(self):
        """Returns whether a simple bind was used, or ``False`` for an uninitialized connection."""

        return getattr(_thread_locals, "simple_bind", False)

    def search(self, dn, filter, attributes):
        """Search LDAP and return an :class:`LDAPResult`.

        Search LDAP with the given dn and filter and return the given
        attributes in an :class:`LDAPResult` object.

        Args:
            dn
                The string representation of the distinguished name
                (DN) of the entry at which to start the search.
            filter
                The string representation of the filter to apply to
                the search.
            attributes
                A list of LDAP attributes (as strings) to retrieve.

        Returns:
            An :class:`LDAPResult` object.

        Raises:
            Should raise stuff but it doesn't yet

        """
        logger.debug("Searching ldap - dn: {}, filter: {}, " "attributes: {}".format(dn, filter, attributes))

        # ldap3 requires the filter to be in parenthesis
        if not filter.endswith(')'):
            filter = "(%s)" % filter

        self.conn.search(dn, filter, attributes=attributes)
        return self.conn.response

    def user_attributes(self, dn, attributes):
        """Fetch a list of attributes of the specified user.

        Fetch LDAP attributes of a tjhsstStudent or a tjhsstTeacher. The
        :class:`LDAPResult` will contain an empty set of results if the
        user does not exist.

        Args:
            dn
                The full DN of the user
            attributes
                A list of the LDAP fields to fetch (strings)

        Returns:
            :class:`LDAPResult` object (empty if no results)

        """
        logger.debug("Fetching attributes '{}' of user " "{}".format(str(attributes), dn))

        filter = LDAPFilter.all_users()

        try:
            r = self.search(dn, filter, attributes=attributes)
        except ldap3.LDAPNoSuchObjectResult:
            logger.warning("No such user " + dn)
            raise
        return LDAPResult(r)

    def photo_attributes(self, dn, attributes):
        """Fetch a list of attributes of the specified photo for a user.

        Fetch LDAP attributes of an iodinePhoto. The :class:`LDAPResult` will
        contain an empty set of results if the photo does not exist.

        Args:
            dn
                The full DN of the photo
            attributes
                A list of the LDAP fields to fetch (strings)

        Returns:
            :class:`LDAPResult` object (empty if no results)

        """
        logger.debug("Fetching attributes '{}' of photo " "{}".format(str(attributes), dn))

        filter = "(objectClass=iodinePhoto)"

        try:
            r = self.search(dn, filter, attributes)
        except ldap3.LDAPNoSuchObjectResult:
            logger.warning("No such photo " + dn)
            raise
        return LDAPResult(r)

    def class_attributes(self, dn, attributes):
        """Fetch a list of attributes of the specified class.

        Fetch LDAP attributes of a tjhsstClass. The :class:`LDAPResult`
        will contain an empty set of results if the class does not
        exist.

        Args:
            dn
                The full DN of the class
            attributes
                A list of the LDAP fields to fetch (strings)

        Returns:
            :class:`LDAPResult` object (empty if no results)

        """
        logger.debug("Fetching attributes '" + str(attributes) + "' of class " + dn)
        filter = '(objectclass=tjhsstClass)'

        try:
            r = self.search(dn, filter, attributes=attributes)
        except ldap3.LDAPNoSuchObjectResult:
            logger.warning("No such class " + dn)
            raise
        return LDAPResult(r)

    def set_attribute(self, dn, attribute, value):
        if isinstance(value, (list, tuple)):
            value = [str(v) for v in value]
        else:
            value = [value]
        self.conn.modify(dn, {attribute: [(ldap3.MODIFY_REPLACE, value)]})


class LDAPResult(object):
    """Represents the result of an LDAP query.

    LDAPResult stores the raw result of an LDAP query and can process
    the results in various ways.

    Attributes:
        result
            The raw result of an LDAP query

    """

    def __init__(self, result):
        self.result = result

    def first_result(self):
        """Fetch the first LDAP object in the response."""
        if len(self.result) > 0:
            return self.result[0]['attributes']
        else:
            return []

    def results_array(self):
        """Return the full array of results."""
        return self.result


@receiver(request_finished, dispatch_uid="close_ldap_connection", sender=WSGIHandler)
def close_ldap_connection(sender, **kwargs):
    """Closes the request's LDAP connection and clears up thread locals.

    Listens for the request_finished signal from Django and upon
    receipt, unbinds from the directory, terminates the current
    association, and frees resources.

    It would be nice if we could leave the connections open in a pool,
    but it looks like rebinding on an open connection isn't possible
    with GSSAPI binds.

    """
    if hasattr(_thread_locals, "ldap_conn"):
        if _thread_locals.ldap_conn is not None:
            if _thread_locals.ldap_conn.bound:
                _thread_locals.ldap_conn.unbind()
            _thread_locals.ldap_conn = None
            logger.info("LDAP connection closed.")
    if hasattr(_thread_locals, "simple_bind"):
        del _thread_locals.simple_bind
