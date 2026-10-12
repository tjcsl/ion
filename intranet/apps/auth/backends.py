import enum
import logging

import ldap
import pam
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django_auth_ldap.backend import LDAPBackend
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


class TJHSSTLDAPBackend(LDAPBackend):
    """LDAP authentication backend that creates users based on group membership."""

    def authenticate_ldap_user(self, ldap_user, password):
        """Authenticate LDAP user and create Django user if authorized."""
        # First check if user is in authorized group
        if not self._check_group_membership(ldap_user):
            logger.warning("LDAP user %s not in authorized group", ldap_user.dn)
            return None

        # Check if Django user exists
        try:
            user = get_user_model().objects.get(username__iexact=ldap_user.username)
            logger.debug("Existing Django user found for LDAP user %s", ldap_user.username)
            return user
        except get_user_model().DoesNotExist:
            # Create new user from LDAP data
            return self._create_user_from_ldap(ldap_user)

    def _check_group_membership(self, ldap_user):
        """Check if LDAP user is member of authorized group."""
        target_group = "cn=people,cn=groups,cn=accounts,dc=tjhsst,dc=edu"
        
        if hasattr(ldap_user, 'group_dns'):
            return target_group in ldap_user.group_dns
        
        # Fallback: check memberOf attribute
        member_of = ldap_user.attrs.get('memberOf', [])
        return target_group in member_of

    def _create_user_from_ldap(self, ldap_user):
        """Create Django user from LDAP attributes."""
        User = get_user_model()
        
        # Extract user data from LDAP
        username = ldap_user.username
        first_name = ldap_user.attrs.get('givenName', [''])[0]
        last_name = ldap_user.attrs.get('sn', [''])[0]
        email = ldap_user.attrs.get('mail', [''])[0]
        
        # Determine user type and graduation year - fail if invalid
        user_info = self._determine_user_info(ldap_user)
        if user_info is None:
            logger.warning("Invalid gidNumber for LDAP user %s, authentication failed", username)
            return None
            
        user_type, graduation_year = user_info
        
        # Create user
        user = User.objects.create(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            user_type=user_type,
            graduation_year=graduation_year
        )
        
        logger.info("Created new Django user from LDAP: %s (type: %s, grad_year: %s)", 
                   username, user_type, graduation_year)
        return user

    def _determine_user_info(self, ldap_user):
        """Determine user type and graduation year from LDAP attributes.
        
        Returns:
            tuple (user_type, graduation_year) if valid, None if invalid gidNumber
        """
        # Get gidNumber - this is required and must be valid
        gid_number = ldap_user.attrs.get('gidNumber', [None])[0]
        if not gid_number:
            logger.warning("No gidNumber found for LDAP user %s", ldap_user.dn)
            return None
            
        try:
            gid_number = int(gid_number)
        except (ValueError, TypeError):
            logger.warning("Invalid gidNumber format for LDAP user %s: %s", ldap_user.dn, gid_number)
            return None

        # Determine user type from group membership
        staff_group = "cn=staff,cn=groups,cn=accounts,dc=tjhsst,dc=edu"
        student_group = "cn=students,cn=groups,cn=accounts,dc=tjhsst,dc=edu"
        
        member_of = ldap_user.attrs.get('memberOf', [])
        if hasattr(ldap_user, 'group_dns'):
            groups = ldap_user.group_dns
        else:
            groups = member_of

        # Validate gidNumber and determine user type
        if staff_group in groups:
            if gid_number == 1984:
                return 'staff', None
            else:
                logger.warning("Staff member %s has invalid gidNumber: %d (expected 1984)", ldap_user.dn, gid_number)
                return None
        elif student_group in groups:
            if 1985 <= gid_number <= 9999:
                return 'student', gid_number
            else:
                logger.warning("Student %s has invalid gidNumber: %d (expected 1985-9999)", ldap_user.dn, gid_number)
                return None
        else:
            logger.warning("LDAP user %s not in staff or students group", ldap_user.dn)
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


class TJHSSTLDAPBackend(LDAPBackend):
    """LDAP authentication backend that creates users based on group membership."""

    def authenticate_ldap_user(self, ldap_user, password):
        """Authenticate LDAP user and create Django user if authorized."""
        # First check if user is in authorized group
        if not self._check_group_membership(ldap_user):
            logger.warning("LDAP user %s not in authorized group", ldap_user.dn)
            return None

        # Check if Django user exists
        try:
            user = get_user_model().objects.get(username__iexact=ldap_user.username)
            logger.debug("Existing Django user found for LDAP user %s", ldap_user.username)
            return user
        except get_user_model().DoesNotExist:
            # Create new user from LDAP data
            return self._create_user_from_ldap(ldap_user)

    def _check_group_membership(self, ldap_user):
        """Check if LDAP user is member of authorized group."""
        target_group = "cn=people,cn=groups,cn=accounts,dc=tjhsst,dc=edu"
        
        if hasattr(ldap_user, 'group_dns'):
            return target_group in ldap_user.group_dns
        
        # Fallback: check memberOf attribute
        member_of = ldap_user.attrs.get('memberOf', [])
        return target_group in member_of

    def _create_user_from_ldap(self, ldap_user):
        """Create Django user from LDAP attributes."""
        User = get_user_model()
        
        # Extract user data from LDAP
        username = ldap_user.username
        first_name = ldap_user.attrs.get('givenName', [''])[0]
        last_name = ldap_user.attrs.get('sn', [''])[0]
        email = ldap_user.attrs.get('mail', [''])[0]
        
        # Determine user type and graduation year - fail if invalid
        user_info = self._determine_user_info(ldap_user)
        if user_info is None:
            logger.warning("Invalid gidNumber for LDAP user %s, authentication failed", username)
            return None
            
        user_type, graduation_year = user_info
        
        # Create user
        user = User.objects.create(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            user_type=user_type,
            graduation_year=graduation_year
        )
        
        logger.info("Created new Django user from LDAP: %s (type: %s, grad_year: %s)", 
                   username, user_type, graduation_year)
        return user

    def _determine_user_info(self, ldap_user):
        """Determine user type and graduation year from LDAP attributes.
        
        Returns:
            tuple (user_type, graduation_year) if valid, None if invalid gidNumber
        """
        # Get gidNumber - this is required and must be valid
        gid_number = ldap_user.attrs.get('gidNumber', [None])[0]
        if not gid_number:
            logger.warning("No gidNumber found for LDAP user %s", ldap_user.dn)
            return None
            
        try:
            gid_number = int(gid_number)
        except (ValueError, TypeError):
            logger.warning("Invalid gidNumber format for LDAP user %s: %s", ldap_user.dn, gid_number)
            return None

        # Determine user type from group membership
        staff_group = "cn=staff,cn=groups,cn=accounts,dc=tjhsst,dc=edu"
        student_group = "cn=students,cn=groups,cn=accounts,dc=tjhsst,dc=edu"
        
        member_of = ldap_user.attrs.get('memberOf', [])
        if hasattr(ldap_user, 'group_dns'):
            groups = ldap_user.group_dns
        else:
            groups = member_of

        # Validate gidNumber and determine user type
        if staff_group in groups:
            if gid_number == 1984:
                return 'staff', None
            else:
                logger.warning("Staff member %s has invalid gidNumber: %d (expected 1984)", ldap_user.dn, gid_number)
                return None
        elif student_group in groups:
            if 1985 <= gid_number <= 9999:
                return 'student', gid_number
            else:
                logger.warning("Student %s has invalid gidNumber: %d (expected 1985-9999)", ldap_user.dn, gid_number)
                return None
        else:
            logger.warning("LDAP user %s not in staff or students group", ldap_user.dn)
            return None
