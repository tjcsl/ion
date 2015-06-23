# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pexpect
import uuid
import os
import logging
from django.contrib.auth.hashers import check_password
from django.core import exceptions
from intranet import settings
from ..users.models import User

logger = logging.getLogger(__name__)


class KerberosAuthenticationBackend(object):

    """Authenticate using Kerberos. This is the default
    authentication backend.

    """

    @staticmethod
    def get_kerberos_ticket(username, password):
        """Attempts to create a Kerberos ticket for a user.

        Args:
            username
                The username.
            password
                The password.

        Returns:
            Boolean indicating success or failure of ticket creation

        """


        def kinit_timeout_handle(username, realm):
            """Check if the user exists before we throw an error.
            If the user does not exist in LDAP, only throw a warning.
            """

            try:
                user = User.get_user(username=username)
            except User.DoesNotExist:
                logger.warning("kinit timed out for {}@{} (invalid user)".format(username, realm))
                return

            logger.critical("kinit timed out for {}@{}".format(username, realm))

        cache = "/tmp/ion-" + str(uuid.uuid4())

        logger.debug("Setting KRB5CCNAME to 'FILE:{}'".format(cache))
        os.environ["KRB5CCNAME"] = "FILE:" + cache

        try:
            realm = settings.CSL_REALM
            kinit = pexpect.spawnu("/usr/bin/kinit {}@{}".format(username, realm))
            kinit.expect(":")
            kinit.sendline(password)
            kinit.expect(pexpect.EOF)
            kinit.close()
            exitstatus = kinit.exitstatus
        except pexpect.TIMEOUT:
            kinit_timeout_handle(username, realm)
            exitstatus = 1

        if exitstatus != 0:
            realm = settings.AD_REALM
            try:
                kinit = pexpect.spawnu("/usr/bin/kinit {}@{}".format(username, realm))
                kinit.expect(":", timeout=5)
                kinit.sendline(password)
                kinit.expect(pexpect.EOF)
                kinit.close()
                exitstatus = kinit.exitstatus
            except pexpect.TIMEOUT:
                kinit_timeout_handle(username, realm)
                exitstatus = 1

        if exitstatus == 0:
            logger.debug("Kerberos authorized {}@{}".format(username, realm))
            return True
        else:
            logger.debug("Kerberos failed to authorize {}".format(username))
            if "KRB5CCNAME" in os.environ:
                del os.environ["KRB5CCNAME"]
            return False

    def authenticate(self, username=None, password=None):
        """Authenticate a username-password pair.

        Creates a new user if one is not already in the database.

        Args:
            username
                The username of the `User` to authenticate.
            password
                The password of the `User` to authenticate.

        Returns:
            `User`

        NOTE: None is returned when the user account does not exist. However,
        if the account exists but does not exist in LDAP, which is the case for
        former and future students who do not have Intranet access, a dummy user
        is returned that has the flag is_active=False. (The is_active property in
        the User class returns False when the username starts with "INVALID_USER".)

        """
        krb_ticket = self.get_kerberos_ticket(username, password)

        if not krb_ticket:
            return None
        else:
            logger.debug("Authentication successful")
            try:
                user = User.get_user(username=username)
            except User.DoesNotExist:
                # Shouldn't happen
                logger.error("User {} successfully authenticated but not found "
                             "in LDAP.".format(username))
                
                user, status = User.objects.get_or_create(username="INVALID_USER", id=99999)
                return user

            return user

    def get_user(self, user_id):
        """Returns a user, given his or her user id. Required for a
        custom authentication backend.

        Args:
            user_id
                The user id of the user to fetch.

        Returns:
            User or None

        """
        try:
            return User.get_user(id=user_id)
        except User.DoesNotExist:
            return None


class MasterPasswordAuthenticationBackend(object):

    """Authenticate as any user against a master password whose hash is
    in secret.py. Forces a simple LDAP bind.

    """

    def authenticate(self, username=None, password=None):
        """Authenticate a username-password pair.

        Creates a new user if one is not already in the database.

        Args:
            username
                The username of the `User` to authenticate.
            password
                The master password.

        Returns:
            `User`

        """

        if check_password(password, settings.MASTER_PASSWORD):
            try:
                user = User.get_user(username=username)
            except User.DoesNotExist:
                logger.debug("Master password correct, user does not exist")
                return None

            logger.debug("Authentication with master password successful")
            return user
        logger.debug("Master password authentication failed")
        return None

    def get_user(self, user_id):
        """Returns a user, given his or her user id. Required for a
        custom authentication backend.

        Args:
            user_id
                The user id of the user to fetch.

        Returns:
            User or None

        """
        try:
            return User.get_user(id=user_id)
        except User.DoesNotExist:
            return None
