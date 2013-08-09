import pexpect
import uuid
import os
import logging
from intranet import settings
from intranet.apps.users.models import User

logger = logging.getLogger(__name__)


class KerberosAuthenticationBackend(object):
    @staticmethod
    def get_kerberos_ticket(username, password):
        """Attempts to create a Kerberos ticket for a user.

        Args:
            - username -- The username.
            - password -- The password.

        Returns:
            Boolean indicating success or failure of ticket creation
        """

        cache = "/tmp/ion-" + str(uuid.uuid4())

        logger.debug("Setting KRB5CCNAME to " + cache)
        os.environ['KRB5CCNAME'] = cache

        kinit = pexpect.spawn("/usr/bin/kinit {}@{}".format(username, settings.CSL_REALM))
        kinit.expect("{}@{}'s Password:".format(username, settings.CSL_REALM))
        kinit.sendline(password)
        kinit.expect(pexpect.EOF)
        kinit.close()

        exitstatus = kinit.exitstatus
        realm = settings.CSL_REALM

        if exitstatus != 0:
            kinit = pexpect.spawn("/usr/bin/kinit {}@{}".format(username, settings.AD_REALM))
            kinit.expect("{}@{}'s Password:".format(username, settings.AD_REALM))
            kinit.sendline(password)
            kinit.expect(pexpect.EOF)
            kinit.close()
            exitstatus = kinit.exitstatus
            realm = settings.AD_REALM

        if exitstatus == 0:
            logger.info("Kerberos authorized {}@{}".format(username, realm))
            kgetcred = pexpect.spawn("/usr/bin/kgetcred ldap/{}@{}".format(settings.HOST, settings.LDAP_REALM))
            kgetcred.expect(pexpect.EOF)
            kgetcred.close()

            if kgetcred.exitstatus == 0:
                logger.info("Kerberos got ticket for ldap service")
                return True
            else:
                logger.error("Kerberos failed to get ticket for LDAP service")
                os.system("/usr/bin/kdestroy")
                # TODO: Try simple bind
                return False
        else:
            os.system("/usr/bin/kdestroy")
            return False

    def authenticate(self, username=None, password=None):
        """Authenticate a username-password pair.

        Creates a new user if one is not already in the database.

        Args:
            - username -- The username of the `User` to authenticate.
            - password -- The password of the `User` to authenticate.

        Returns:
            `User`

        """
        if not self.get_kerberos_ticket(username, password):
            return None
        else:
            logger.info("Authentication successful")
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                logger.info("First login - creating new user in sql database")
                user = User()
                user.username = username
                user.id = user.ion_id
                user.set_unusable_password()
                user.save()
            return user

    def get_user(self, user_id):
        """Returns a user, given his or her user id. Required for a
        custom authentication backend.

        Args:
            user_id: The user id of the user to fetch.

        Returns:
            User or None

        """
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
