from oauth2_provider.views.application import ApplicationUpdate


class ApplicationUpdateView(ApplicationUpdate):  # pylint: disable=too-many-ancestors; Beyond our control
    fields = ["name", "client_id", "client_secret", "client_type", "authorization_grant_type", "redirect_uris"]
