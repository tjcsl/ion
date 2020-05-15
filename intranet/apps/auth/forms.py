import logging

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.forms import widgets

logger = logging.getLogger(__name__)


class AuthenticateForm(AuthenticationForm):
    """Implements a login form.

    Attributes:
        username
            The username text field.
        password
            The password text field.

    """

    username = forms.CharField(
        required=True,
        label="",
        widget=widgets.TextInput(attrs={"placeholder": "Username", "aria-label": "Enter Username"}),
        error_messages={"required": "Invalid username", "inactive": "Access disallowed."},
    )
    password = forms.CharField(
        required=True,
        strip=False,
        label="",
        widget=widgets.PasswordInput(attrs={"placeholder": "Password", "aria-label": "Enter Password"}),
        error_messages={"required": "Invalid password", "inactive": "Access disallowed."},
    )

    trust_device = forms.BooleanField(required=False, label="Trust this device", label_suffix="")

    def is_valid(self):
        """Validates the username and password in the form."""
        form = super(AuthenticateForm, self).is_valid()
        for f, error in self.errors.items():
            if f != "__all__":
                self.fields[f].widget.attrs.update({"class": "error", "placeholder": ", ".join(list(error))})
            else:
                errors = list(error)
                if "This account is inactive." in errors:
                    message = "Intranet access restricted"
                else:
                    message = "Invalid password"
                self.fields["password"].widget.attrs.update({"class": "error", "placeholder": message})

        return form


class ResetLoginAttemptsEmailForm(forms.Form):
    user_account = forms.CharField(max_length=30, required=True)

    def is_valid(self):
        form = super(ResetLoginAttemptsEmailForm, self).is_valid()
        return get_user_model().objects.filter(username=self.cleaned_data["user_account"]).exists() and form


class ResetLoginForm(forms.Form):
    user_account = forms.CharField(max_length=30, required=False)
    reset_all = forms.BooleanField(required=False)

    def is_valid(self):
        form = super(ResetLoginForm, self).is_valid()
        if self.cleaned_data["user_account"] != "":
            return get_user_model().objects.filter(username=self.cleaned_data["user_account"]).exists() and form
        return form
