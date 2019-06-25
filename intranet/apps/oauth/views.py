from oauth2_provider.views.application import ApplicationUpdate


class ApplicationUpdateView(ApplicationUpdate):
    fields = ["name", "client_id", "client_secret", "client_type", "authorization_grant_type", "redirect_uris"]
