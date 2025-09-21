from oauth2_provider.oauth2_validators import OAuth2Validator


class IonOIDCValidator(OAuth2Validator):
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

        return claims
