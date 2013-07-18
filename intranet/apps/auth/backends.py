import pexpect
import uuid
import os
import logging
from intranet.apps.users.models import User

logger = logging.getLogger(__name__)


class KerberosAuthenticationBackend(object):
    @staticmethod
    def get_kerberos_ticket(username, password):
        host = "ion.tjhsst.edu"
        ldap_realm = "CSL.TJHSST.EDU"

        ad_realm = "LOCAL.TJHSST.EDU"
        csl_realm = "CSL.TJHSST.EDU"
        cache = "/tmp/ion-" + str(uuid.uuid4())

        logger.debug("Setting KRB5CCNAME to " + cache)
        os.environ['KRB5CCNAME'] = cache

        kinit = pexpect.spawn("/usr/bin/kinit {}@{}".format(username, csl_realm))
        kinit.expect("{}@{}'s Password:".format(username, csl_realm))
        kinit.sendline(password)
        kinit.expect(pexpect.EOF)
        kinit.close()
        exitstatus = kinit.exitstatus
        realm = csl_realm

        if exitstatus != 0:
            kinit = pexpect.spawn("/usr/bin/kinit {}@{}".format(username, ad_realm))
            kinit.expect("{}@{}'s Password:".format(username, ad_realm))
            kinit.sendline(password)
            kinit.expect(pexpect.EOF)
            kinit.close()
            exitstatus = kinit.exitstatus
            realm = ad_realm

        if kinit.exitstatus == 0:
            logger.debug("Kerberos authorized {}@{}".format(username, realm))
            kgetcred = pexpect.spawn("/usr/bin/kgetcred ldap/{}@{}".format(host, ldap_realm))
            kgetcred.expect(pexpect.EOF)
            kgetcred.close()

            if kgetcred.exitstatus == 0:
                logger.debug("Kerberos got ticket for ldap service")
                return True
            else:
                logger.debug("Kerberos failed to get ticket for LDAP service")
                os.system("/usr/bin/kdestroy")
                # TODO: Try simple bind
                return False
        else:
            os.system("/usr/bin/kdestroy")
            return False

    def authenticate(self, username=None, password=None):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            logger.info("First login - creating new user in sql database")
            user = User()
            user.username = username
            user.pk = user.ion_id
            user.set_unusable_password()
            user.save()

        if self.get_kerberos_ticket(username, password):
            logger.info("Authentication successful")
            return user
        else:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
