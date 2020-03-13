import enum
import logging
import os
import re
import tempfile
from typing import Union

import pexpect
from prometheus_client import Counter, Summary

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password

logger = logging.getLogger(__name__)

kerberos_authenticate = Summary("intranet_kerberos_authenticate", "Kerberos authentication requests")
kerberos_authenticate_failures = Counter("intranet_kerberos_authenticate_failures", "Number of failed Kerberos authentication attempts")
kerberos_authenticate_post_failures = Counter(
    "intranet_kerberos_authenticate_post_failures",
    "Number of Kerberos authentication attempts that failed even though a ticket was successfully obtained (for example, if the user object does not "
    "exist)",
)


class KerberosAuthenticationResult(enum.Enum):
    FAILURE = 0  # Authentication failed
    SUCCESS = 1  # Authentication succeeded
    EXPIRED = -1  # Password expired; needs reset


class KerberosAuthenticationBackend:
    """Authenticate using Kerberos.

    This is the default authentication backend.

    """

    @staticmethod
    def kinit_timeout_handle(username, realm):
        """Check if the user exists before we throw an error."""
        try:
            u = get_user_model().objects.get(username__iexact=username)
        except get_user_model().DoesNotExist:
            logger.warning("kinit timed out for %s@%s (invalid user)", username, realm)
            return

        logger.critical(
            "kinit timed out for %s",
            realm,
            extra={
                "stack": True,
                "data": {"username": username},
                "sentry.interfaces.User": {"id": u.id, "username": username, "ip_address": "127.0.0.1"},
            },
        )

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

        # We should not try to authenticate with an empty password
        if password == "":
            return KerberosAuthenticationResult.FAILURE, False

        krb5cc_fd, krb5ccname = tempfile.mkstemp(prefix="ion-", text=False)
        os.close(krb5cc_fd)

        # Attempt to authenticate against CSL Kerberos realm
        realm = settings.CSL_REALM
        result = KerberosAuthenticationBackend.try_single_kinit(
            username=username, realm=realm, password=password, timeout=settings.KINIT_TIMEOUT, krb5ccname=krb5ccname
        )

        authenticated_through_AD = False

        if result == KerberosAuthenticationResult.FAILURE:
            # Attempt to authenticate against the Active Directory Kerberos realm
            authenticated_through_AD = True

            realm = settings.AD_REALM
            result = KerberosAuthenticationBackend.try_single_kinit(
                username=username, realm=realm, password=password, timeout=settings.KINIT_TIMEOUT, krb5ccname=krb5ccname
            )

        if result == KerberosAuthenticationResult.SUCCESS:
            logger.debug("Kerberos authorized %s@%s - %r", username, realm, authenticated_through_AD)
        else:
            logger.debug("Kerberos failed to authorize %s - %r", username, authenticated_through_AD)

        return result, authenticated_through_AD

    @staticmethod
    def try_single_kinit(*, username: str, realm: str, password: str, krb5ccname: str, timeout: Union[int, float]) -> KerberosAuthenticationResult:
        try:
            kinit = pexpect.spawn("/usr/bin/kinit", ["-c", krb5ccname, "{}@{}".format(username, realm)], timeout=timeout, encoding="utf-8")
            kinit.expect(":")
            kinit.sendline(password)
            returned = kinit.expect([pexpect.EOF, "password:"])
            if returned == 1:
                logger.debug("Password for %s@%s expired, needs reset", username, realm)
                return KerberosAuthenticationResult.EXPIRED
            kinit.close()

            return KerberosAuthenticationResult.SUCCESS if kinit.exitstatus == 0 else KerberosAuthenticationResult.FAILURE
        except pexpect.TIMEOUT:
            KerberosAuthenticationBackend.kinit_timeout_handle(username, realm)
            return KerberosAuthenticationResult.FAILURE

    @kerberos_authenticate.time()
    def authenticate(self, request, username=None, password=None):
        """Authenticate a username-password pair.

        Creates a new user if one is not already in the database.

        Args:
            username
                The username of the `User` to authenticate.
            password
                The password of the `User` to authenticate.

        Returns:
            `User`

        """

        if not isinstance(username, str):
            return None

        # remove all non-alphanumerics
        username = re.sub(r"\W", "", username).lower()

        result, ad_auth = self.get_kerberos_ticket(username, password)

        if result == KerberosAuthenticationResult.SUCCESS:
            logger.debug("Authentication successful")

            try:
                user = get_user_model().objects.get(username__iexact=username)
            except get_user_model().DoesNotExist:
                kerberos_authenticate_failures.inc()
                kerberos_authenticate_post_failures.inc()
                return None

            if user.user_type == "student" and ad_auth:
                kerberos_authenticate_failures.inc()
                kerberos_authenticate_post_failures.inc()
                # Block authentication for students who authenticated via AD
                return None

            return user
        elif result == KerberosAuthenticationResult.EXPIRED:
            user, _ = get_user_model().objects.get_or_create(username="RESET_PASSWORD", user_type="service", id=999999)
            return user
        else:
            kerberos_authenticate_failures.inc()
            return None

    def get_user(self, user_id):
        """Returns a user, given his or her user id. Required for a custom authentication backend.
        Args:
            user_id
                The user id of the user to fetch.
        Returns:
            User or None
        """
        try:
            return get_user_model().objects.get(id=user_id)
        except get_user_model().DoesNotExist:
            return None


class MasterPasswordAuthenticationBackend:
    """Authenticate as any user against a master password whose hash is in secret.py.

    """

    def authenticate(self, request, username=None, password=None):
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
        if not hasattr(settings, "MASTER_PASSWORD"):
            logging.debug("Master password not set.")
            return None
        if check_password(password, settings.MASTER_PASSWORD):
            try:
                user = get_user_model().objects.get(username__iexact=username)
            except get_user_model().DoesNotExist:
                if settings.MASTER_NOTIFY:
                    logger.critical("Master password authentication FAILED due to invalid username %s", username)
                logger.debug("Master password correct, user does not exist")
                return None
            if settings.MASTER_NOTIFY:
                logger.critical("Master password authentication SUCCEEDED with username %s", username)
            logger.debug("Authentication with master password successful")
            return user
        logger.debug("Master password authentication failed")
        return None

    def get_user(self, user_id):
        """Returns a user, given his or her user id. Required for a custom authentication backend.
        Args:
            user_id
                The user id of the user to fetch.
        Returns:
            User or None
        """
        try:
            return get_user_model().objects.get(id=user_id)
        except get_user_model().DoesNotExist:
            return None
