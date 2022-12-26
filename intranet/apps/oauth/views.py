from oauth2_provider.models import get_application_model
from oauth2_provider.views.application import ApplicationDelete, ApplicationRegistration, ApplicationUpdate

from django.forms.models import modelform_factory
from django.shortcuts import render

from .models import BlankModel


class ApplicationRegistrationView(ApplicationRegistration):
    """
    Custom registration view.
    Check that the user has OAuth and API access before allowing them to register an application.
    Disable showing algorithm field.
    Disable editing client_id and client_secret fields.
    Note that there are three layers of permission checking: at the template level, form level, and response level.
    This view handles the form and response levels.
    """

    def get_form_class(self):
        """
        Returns the form class for the application model
        """
        if not self.request.user.oauth_and_api_access:
            return modelform_factory(BlankModel, fields=())

        form = modelform_factory(
            get_application_model(),
            fields=(
                "name",
                "client_id",
                "client_secret",
                "client_type",
                "authorization_grant_type",
                "redirect_uris",
            ),
        )

        # make client_id and client_secret read-only
        form.base_fields["client_id"].widget.attrs["readonly"] = True
        form.base_fields["client_secret"].widget.attrs["readonly"] = True

        return form

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return self.handle_no_permission()
        if not user.oauth_and_api_access:
            return render(
                self.request,
                "error/403.html",
                {"reason": "You are not authorized to manage OAuth applications. This incident has been reported."},
                status=403,
            )
        return super().dispatch(request, *args, **kwargs)


class ApplicationUpdateView(ApplicationUpdate):
    """
    Custom update view to disable showing the algorithm, client_id and client_secret fields
    and check if the user can update applications.
    """

    def get_form_class(self):
        """
        Returns the form class for the application model
        """
        if not self.request.user.oauth_and_api_access:
            return modelform_factory(BlankModel, fields=())

        return modelform_factory(
            get_application_model(),
            fields=(
                "name",
                "client_type",
                "authorization_grant_type",
                "redirect_uris",
            ),
        )

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return self.handle_no_permission()
        if not user.oauth_and_api_access:
            return render(
                self.request,
                "error/403.html",
                {"reason": "You are not authorized to manage OAuth applications. This incident has been reported."},
                status=403,
            )
        return super().dispatch(request, *args, **kwargs)


class ApplicationDeleteView(ApplicationDelete):
    """Custom delete view to check if the user can delete applications."""

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return self.handle_no_permission()
        if not user.oauth_and_api_access:
            return render(
                self.request,
                "error/403.html",
                {"reason": "You are not authorized to manage OAuth applications. This incident has been reported."},
                status=403,
            )
        return super().dispatch(request, *args, **kwargs)
