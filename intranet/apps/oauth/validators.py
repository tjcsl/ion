import logging

from oauth2_provider.oauth2_validators import OAuth2Validator

logger = logging.getLogger(__name__)


class IonOIDCValidator(OAuth2Validator):
    oidc_claim_scope = OAuth2Validator.oidc_claim_scope.copy()
    oidc_claim_scope.update({"groups": "groups", "is_sysadmin": "groups"})  # manually add it since groups is not part of the standard OIDC spec

    def get_additional_claims(self, request):
        claims = {}
        user = request.user

        if "profile" in request.scopes:
            claims.update(
                {
                    "given_name": user.first_name,
                    "family_name": user.last_name,
                    "name": f"{user.first_name} {user.last_name}",
                    "preferred_username": user.username,
                }
            )

        if "email" in request.scopes:
            claims.update(
                {
                    "email": user.notification_email,
                    "email_verified": True,  # This is not always true but for our purposes it doesn't matter
                }
            )

        if "groups" in request.scopes:
            claims.update(
                {
                    "groups": list(user.groups.values_list("name", flat=True)),
                    "is_sysadmin": user.groups.filter(name="Sysadmin(R) -- Permissions").exists(),
                }
            )

        return claims
