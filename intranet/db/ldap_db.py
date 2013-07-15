import logging
import ldap
import ldap.sasl
from django.core import signals
from django.dispatch import receiver
from intranet import settings

logger = logging.getLogger(__name__)

BASE_DN = "dc=tjhsst,dc=edu"
USER_DN = "ou=people,dc=tjhsst,dc=edu"
SCHEDULE_DN = "ou=schedule,dc=tjhsst,dc=edu"


class Connection():
    conn = None

    def __init__(self):
        if not Connection.conn:
            logger.debug("Connecting to LDAP")
            Connection.conn = ldap.initialize(settings.LDAP_SERVER)
            auth_tokens = ldap.sasl.gssapi()
            Connection.conn.sasl_interactive_bind_s('', auth_tokens)

    def search(self, dn, filter, attributes):
        return Connection.conn.search_s(dn, ldap.SCOPE_SUBTREE, filter, attributes)

    def user_attribute(self, username, attribute):
        dn = 'iodineUid={},{}'.format(username, USER_DN)
        logger.debug(dn)
        filter = '(objectclass=tjhsstStudent)'
        try:
            r = self.search(dn, filter, [attribute])
        except ldap.NO_SUCH_OBJECT:
            logger.error("No such object " + dn)
            return ''
        except ldap.NO_SUCH_ATTRIBUTE:
            logger.error("No such attribute: " + attribute + " for dn: " + dn)
            return ''
        except ldap.NO_RESULTS_RETURNED:
            logger.debug("No results found")
            return ''

        return r
