# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pexpect
import uuid
import os
import logging
from intranet import settings
from ..users.models import User

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
        # username = unicode(username)
        # password = unicode(password)

        logger.debug("Setting KRB5CCNAME to 'FILE:{}'".format(cache))
        os.environ["KRB5CCNAME"] = "FILE:" + cache

        kinit = pexpect.spawnu("/usr/bin/kinit {}@{}".format(username, settings.CSL_REALM))
        kinit.expect("{}@{}'s Password:".format(username, settings.CSL_REALM))
        kinit.sendline(password)
        kinit.expect(pexpect.EOF)
        kinit.close()

        exitstatus = kinit.exitstatus
        realm = settings.CSL_REALM

        if exitstatus != 0:
            kinit = pexpect.spawnu("/usr/bin/kinit {}@{}".format(username, settings.AD_REALM))
            kinit.expect("{}@{}'s Password:".format(username, settings.AD_REALM))
            kinit.sendline(password)
            kinit.expect(pexpect.EOF)
            kinit.close()
            exitstatus = kinit.exitstatus
            realm = settings.AD_REALM

        if exitstatus == 0:
            logger.debug("Kerberos authorized {}@{}".format(username, realm))
            kgetcred = pexpect.spawnu("/usr/bin/kgetcred ldap/{}@{}".format(settings.HOST, settings.LDAP_REALM))
            kgetcred.expect(pexpect.EOF)
            kgetcred.close()

            if kgetcred.exitstatus == 0:
                logger.debug("Kerberos got ticket for ldap service")
                return True
            else:
                logger.error("Kerberos failed to get ticket for LDAP service")
                os.system("/usr/bin/kdestroy")
                return False
        else:
            os.system("/usr/bin/kdestroy")
            return False

    def authenticate(self, username=None, password=None):
        """Authenticate using a master password. A simple LDAP bind will
        be used because a kerberos cache can't be created without a
        password.

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
            logger.debug("Authentication successful")
            try:
                user = User.get_user(username=username)
            except User.DoesNotExist:
                # Shouldn't happen
                logger.error("User successfully authenticated but not found "
                             "in LDAP.")
                return None

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


class MasterPasswordAuthenticationBackend(object):
    """
    Authenticate against the settings ADMIN_LOGIN and ADMIN_PASSWORD.

    Use the login name, and a hash of the password. For example:

    ADMIN_LOGIN = 'admin'
    ADMIN_PASSWORD = 'sha1$4e987$afbcf42e21bd417fb71db8c66b321e9fc33051de'
    """

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
            logger.debug("Authentication successful")
            try:
                user = User.get_user(username=username)
            except User.DoesNotExist:
                # Shouldn't happen
                logger.error("User successfully authenticated but not found "
                             "in LDAP.")
                return None

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

    def authenticate(self, username=None, password=None):
        login_valid = (settings.ADMIN_LOGIN == username)
        pwd_valid = check_password(password, settings.ADMIN_PASSWORD)
        if login_valid and pwd_valid:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                # Create a new user. Note that we can set password
                # to anything, because it won't be checked; the password
                # from settings.py will.
                user = User(username=username, password='get from settings.py')
                user.is_staff = True
                user.is_superuser = True
                user.save()
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
