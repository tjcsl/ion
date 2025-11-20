from typing import Any, Optional
from django.db import models
from django.utils.translation import ugettext_lazy as _
from .settings import oauth2_settings as oauth2_settings

class AbstractApplication(models.Model):
    CLIENT_CONFIDENTIAL = ...  # type: str
    CLIENT_PUBLIC = ...  # type: str
    CLIENT_TYPES = ...  # type: Any
    GRANT_AUTHORIZATION_CODE = ...  # type: str
    GRANT_IMPLICIT = ...  # type: str
    GRANT_PASSWORD = ...  # type: str
    GRANT_CLIENT_CREDENTIALS = ...  # type: str
    GRANT_TYPES = ...  # type: Any
    client_id = ...  # type: Any
    user = ...  # type: Any
    help_text = ...  # type: Any
    redirect_uris = ...  # type: Any
    client_type = ...  # type: Any
    authorization_grant_type = ...  # type: Any
    client_secret = ...  # type: Any
    name = ...  # type: Any
    skip_authorization = ...  # type: Any
    class Meta:
        abstract = ...  # type: bool
    @property
    def default_redirect_uri(self): ...
    def redirect_uri_allowed(self, uri): ...
    def clean(self): ...
    def get_absolute_url(self): ...

class Application(AbstractApplication): ...

class Grant(models.Model):
    user = ...  # type: Any
    code = ...  # type: Any
    application = ...  # type: Any
    expires = ...  # type: Any
    redirect_uri = ...  # type: Any
    scope = ...  # type: Any
    def is_expired(self): ...
    def redirect_uri_allowed(self, uri): ...

class AccessToken(models.Model):
    user = ...  # type: Any
    token = ...  # type: Any
    application = ...  # type: Any
    expires = ...  # type: Any
    scope = ...  # type: Any
    def is_valid(self, scopes: Optional[Any] = ...): ...
    def is_expired(self): ...
    def allow_scopes(self, scopes): ...
    def revoke(self): ...
    @property
    def scopes(self): ...

class RefreshToken(models.Model):
    user = ...  # type: Any
    token = ...  # type: Any
    application = ...  # type: Any
    access_token = ...  # type: Any
    def revoke(self): ...

def get_application_model(): ...
def clear_expired(): ...
