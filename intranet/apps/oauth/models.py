from oauth2_provider.models import AbstractApplication

from django.db import models
from django.utils.translation import gettext_lazy as _


class CSLApplication(AbstractApplication):
    """Extends the default OAuth Application model to add CSL-specific information about an OAuth application.
    Disables the implicit, password, and OpenID connect hybrid grant types.
    Disables use of an OIDC algorithm.

    Attributes:
        sanctioned (bool): Whether the application is sanctioned by the tjCSL.
        sanctioned_but_do_not_skip_authorization (bool): Whether to not skip the authorization page for this application even if it is sanctioned.
        user_has_oauth_and_api_access (bool): Whether the user associated with the CSLApplication has OAuth and API access.
    """

    CLIENT_CONFIDENTIAL = "confidential"
    CLIENT_PUBLIC = "public"
    CLIENT_TYPES = (
        (CLIENT_CONFIDENTIAL, _("Confidential")),
        (CLIENT_PUBLIC, _("Public")),
    )

    GRANT_AUTHORIZATION_CODE = "authorization-code"
    GRANT_IMPLICIT = "implicit"
    GRANT_PASSWORD = "password"
    GRANT_CLIENT_CREDENTIALS = "client-credentials"
    GRANT_OPENID_HYBRID = "openid-hybrid"
    GRANT_TYPES = (
        (GRANT_AUTHORIZATION_CODE, _("Authorization code")),
        # Disabled for security reasons
        # (GRANT_IMPLICIT, _("Implicit")),
        # (GRANT_PASSWORD, _("Resource owner password-based")),
        (GRANT_CLIENT_CREDENTIALS, _("Client credentials")),
        # Disabled because we don't support OIDC
        # (GRANT_OPENID_HYBRID, _("OpenID connect hybrid")),
    )

    NO_ALGORITHM = ""
    RS256_ALGORITHM = "RS256"
    HS256_ALGORITHM = "HS256"
    ALGORITHM_TYPES = (
        (NO_ALGORITHM, _("No OIDC support")),
        # Disabled because we don't support OIDC
        # (RS256_ALGORITHM, _("RSA with SHA-2 256")),
        # (HS256_ALGORITHM, _("HMAC with SHA-2 256")),
    )

    name = models.CharField(max_length=255, blank=False)  # make name required
    authorization_grant_type = models.CharField(max_length=32, choices=GRANT_TYPES)
    algorithm = models.CharField(max_length=5, choices=ALGORITHM_TYPES, default=NO_ALGORITHM, blank=True)
    sanctioned = models.BooleanField(default=False, help_text="Whether this application is sanctioned by the tjCSL.")
    skip_authorization = models.BooleanField(
        default=False,
        help_text=(
            "Skip the authorization page for this application. This will automatically be set to true upon save "
            "if this application is marked as sanctioned by the CSL."
        ),
    )
    sanctioned_but_do_not_skip_authorization = models.BooleanField(
        default=False,
        help_text=(
            "Set to true if this application is sanctioned but you do NOT want to skip the authorization page for this application. "
            "Overrides automatically skipping authorization for sanctioned applications."
        ),
    )

    @property
    def user_has_oauth_and_api_access(self):
        return self.user.oauth_and_api_access

    def save(self, *args, **kwargs):
        self.skip_authorization = self.sanctioned or self.skip_authorization
        self.sanctioned_but_do_not_skip_authorization = self.sanctioned and self.sanctioned_but_do_not_skip_authorization
        if self.sanctioned_but_do_not_skip_authorization:
            self.skip_authorization = False
        super().save(*args, **kwargs)


class BlankModel2:
    private_fields = ()
    concrete_fields = ()
    many_to_many = ()


class BlankModel:
    """A blank model to use for modelform_factory for unauthorized users."""

    _meta = BlankModel2
