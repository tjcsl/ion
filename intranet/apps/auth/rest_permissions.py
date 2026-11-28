from oauth2_provider.contrib.rest_framework import TokenHasReadWriteScope
from rest_framework import permissions


class DenyRestrictedPermission(permissions.BasePermission):
    def has_permission(self, request, view) -> bool:
        return request.user and request.user.is_authenticated and not request.user.is_restricted


class ApiAndOauthPermission(permissions.BasePermission):
    def has_permission(self, request, view) -> bool:
        return request.user and request.user.is_authenticated and not request.user.is_restricted and request.user.oauth_and_api_access


class OAuthTokenHasReadWriteScope(TokenHasReadWriteScope):
    """Requires the "read" scope for safe methods and the "write" scope for all other methods
    when the request is authenticated with an OAuth token. Requests that are not authenticated
    with an OAuth token (e.g. session authentication) are not affected.

    This must be included in the permission_classes of every API view that is not public.
    """

    def has_permission(self, request, view) -> bool:
        if not hasattr(request.auth, "scope"):
            return True
        return super().has_permission(request, view)
