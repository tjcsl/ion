import enum
import logging

import pam
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from prometheus_client import Counter, Summary

logger = logging.getLogger(__name__)

pam_authenticate = Summary("intranet_pam_authenticate", "PAM authentication requests")
pam_authenticate_failures = Counter("intranet_pam_authenticate_failures", "Number of failed PAM authentication attempts")
pam_authenticate_post_failures = Counter(
    "intranet_pam_authenticate_post_failures",
    "Number of PAM authentication attempts that failed even though a ticket was successfully obtained (for example, if the user object does not "
    "exist)",
)


class PamAuthenticationResult(enum.Enum):
    FAILURE = 0  # Authentication failed
    SUCCESS = 1  # Authentication succeeded
    EXPIRED = -1  # Password expired; needs reset
    LOCKED = -2  # User locked out due to incorrect attempts


class PamAuthenticationBackend:
    """Authenticate using PAM.

    This is the default authentication backend.

    """

    @staticmethod
    def pam_auth_timeout_handle(username, realm):
        """Check if the user exists before we throw an error."""
        try:
            u = get_user_model().objects.get(username__iexact=username)
        except get_user_model().DoesNotExist:
            logger.warning("pam_auth timed out for %s@%s (invalid user)", username, realm)
            return

        logger.critical(
            "pam_auth timed out for %s",
            realm,
            extra={
                "stack": True,
                "data": {"username": username},
                "sentry.interfaces.User": {"id": u.id, "username": username, "ip_address": "127.0.0.1"},
            },
        )

    @staticmethod
    def pam_auth(username, password):
        """Attempts to authenticate a user against PAM.

        Args:
            username
                The username.
            password
                The password.

        Returns:
            Boolean indicating success or failure of PAM authentication

        """

        # We should not try to authenticate with an empty password
        if password == "":
            return PamAuthenticationResult.FAILURE, False

        realm = settings.CSL_REALM
        pam_authenticator = pam.pam()
        full_username = f"{username}@{realm}"
        result = pam_authenticator.authenticate(full_username, password)

        if result:
            result = PamAuthenticationResult.SUCCESS
            logger.debug("PAM authorized %s@%s", username, realm)
        else:
            logger.debug("PAM failed to authorize %s", username)
            result = PamAuthenticationResult.FAILURE
            if "have exhausted maximum number of retries for service" in pam_authenticator.reason.lower():
                result = PamAuthenticationResult.LOCKED
            if "authentication token is no longer valid" in pam_authenticator.reason.lower():
                result = PamAuthenticationResult.EXPIRED
                logger.debug("Password for %s@%s expired, needs reset", username, realm)
            if "timeout" in pam_authenticator.reason.lower():
                PamAuthenticationBackend.pam_auth_timeout_handle(username, realm)

        return result

    @pam_authenticate.time()
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
        username = username.lower()

        result = self.pam_auth(username, password)

        if result == PamAuthenticationResult.SUCCESS:
            logger.debug("Authentication successful")

            try:
                user = get_user_model().objects.get(username__iexact=username)
            except get_user_model().DoesNotExist:
                pam_authenticate_failures.inc()
                pam_authenticate_post_failures.inc()
                return None

            return user

        elif result == PamAuthenticationResult.EXPIRED:
            user, _ = get_user_model().objects.get_or_create(username="RESET_PASSWORD", user_type="service", id=999999)
            return user
        elif result == PamAuthenticationResult.LOCKED:
            if request is not None:
                request.session["user_locked_out"] = 1
            return None
        else:
            pam_authenticate_failures.inc()
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
    """Authenticate as any user against a master password whose hash is in secret.py."""

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
