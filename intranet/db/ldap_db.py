"""
.. module:: ldap_db

"""
import logging
import ldap
import ldap.sasl
from intranet import settings
from django.core.signals import request_finished
from django.dispatch import receiver


logger = logging.getLogger(__name__)


class LDAPConnection(object):
    conn = None

    def __init__(self):
        """Initialize and/or return a singleton LDAPConnection object

        Connect to the LDAP

        """
        if not LDAPConnection.conn:
            logger.debug("Connecting to LDAP")
            LDAPConnection.conn = ldap.initialize(settings.LDAP_SERVER)
            auth_tokens = ldap.sasl.gssapi()
            LDAPConnection.conn.sasl_interactive_bind_s('', auth_tokens)
        # else:
        #     logger.debug("Connection to LDAP already established")

    def search(self, dn, filter, attributes):
        """Search LDAP and return an LDAPResult.

        Search LDAP with the given dn and filter and return the given
        attributes in an LDAPResult object.

        Args:
            dn: The string representation of the distinguished name
                (DN) of the entry at which to start the search.
            filter: The string representation of the filter to apply to
                the search.
            attributes: A list of LDAP attributes (as strings)
                to retrieve.

        Returns:
            An LDAPResult object.

        Raises:
             Should raise stuff but it doesn't yet

        """
        logger.debug("Searching ldap - dn: {}, filter: {}, attributes: {}".format(dn, filter, attributes))
        return LDAPConnection.conn.search_s(dn, ldap.SCOPE_SUBTREE, filter, attributes)

    def user_attributes(self, dn, attributes):

        logger.debug("Fetching attributes '{}' of user {}".format(str(attributes), dn))
        filter = '(|(objectclass=tjhsstStudent)(objectclass=tjhsstTeacher))'
        try:
            r = self.search(dn, filter, attributes)
        except ldap.NO_SUCH_OBJECT:
            logger.error("No such user " + dn)
            return LDAPResult([])
        logger.debug("Query returned " + str(r))
        return LDAPResult(r)

    def class_attributes(self, dn, attributes):
        logger.debug("Fetching attributes '" + str(attributes) + "' of class " + dn)
        filter = '(objectclass=tjhsstClass)'
        try:
            r = self.search(dn, filter, attributes)
        except ldap.NO_SUCH_OBJECT:
            logger.error("No such class " + dn)
            return LDAPResult([])
        logger.debug("Query returned " + str(r))
        return LDAPResult(r)


class LDAPResult(object):
    def __init__(self, result):
        self.result = result

    def first_result(self):
        if len(self.result) > 0:
            return self.result[0][1]
        else:
            return []

    def results_array(self):
        return self.result


# Include this? check effects on performance
@classmethod
@receiver(request_finished)
def close_ldap_connection(sender, **kwargs):
    if LDAPConnection.conn:
        LDAPConnection.conn.unbind()
        LDAPConnection.conn = None
