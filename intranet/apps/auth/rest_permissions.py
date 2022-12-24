from rest_framework import permissions


class DenyRestrictedPermission(permissions.BasePermission):
    def has_permission(self, request, view) -> bool:
        return request.user and request.user.is_authenticated and not request.user.is_restricted


class ApiAndOauthPermission(permissions.BasePermission):
    def has_permission(self, request, view) -> bool:
        return request.user and request.user.is_authenticated and not request.user.is_restricted and request.user.oauth_and_api_access
