import logging
import ldap
import ldap.sasl
from intranet import settings

logger = logging.getLogger(__name__)


class LDAPConnection(object):
    conn = None

    def __init__(self):
        if not LDAPConnection.conn:
            logger.debug("Connecting to LDAP")
            LDAPConnection.conn = ldap.initialize(settings.LDAP_SERVER)
            auth_tokens = ldap.sasl.gssapi()
            LDAPConnection.conn.sasl_interactive_bind_s('', auth_tokens)

    def search(self, dn, filter, attributes):
        logger.debug("Searching ldap - dn: {}, filter: {}, attributes: {}".format(dn, filter, attributes))
        return LDAPConnection.conn.search_s(dn, ldap.SCOPE_SUBTREE, filter, attributes)

    def user_attributes(self, dn, attributes):
        logger.debug("Fetching attributes '" + str(attributes) + "' of user " + dn)
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
