import logging

from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.forms import widgets

from intranet.apps.auth.widgets import TurnstileField

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
        label="",
        widget=widgets.PasswordInput(attrs={"placeholder": "Password", "aria-label": "Enter Password"}),
        error_messages={"required": "Invalid password", "inactive": "Access disallowed."},
    )
    otp_token = forms.CharField(
        required=False,
        label="",
        widget=widgets.NumberInput(
            attrs={
                "placeholder": "2FA OTP Code",
                "aria-label": "Enter OTP Code",
                "autocomplete": "one-time-code",
                "maxlength": 8,
            }
        ),
        error_messages={"required": "Invalid 2FA OTP token", "inactive": "Access disallowed."},
        help_text="For users with 2FA enabled: Enter the OTP code from your authenticator app. Other users: Leave this field blank.",
    )

    trust_device = forms.BooleanField(required=False, initial=True, label="Remember me", label_suffix="")

    turnstile = TurnstileField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["turnstile"].set_enabled(settings.TURNSTILE_ENABLED)
        # we'll need the request for ip validation
        if hasattr(self, "request") and self.request:
            self.fields["turnstile"].request = self.request

    def is_valid(self):
        """Validates the username and password in the form."""
        form = super().is_valid()
        for f, error in self.errors.items():
            if f != "__all__":
                self.fields[f].widget.attrs.update({"class": "error", "placeholder": ", ".join(list(error))})
            else:
                errors = list(error)
                if "This account is inactive." in errors:
                    message = "Intranet access restricted"
                elif "Invalid turnstile response" in errors:
                    message = "Invalid CAPTCHA. Reload the page and try again."
                else:
                    message = "Invalid password"
                self.fields["password"].widget.attrs.update({"class": "error", "placeholder": message})

        return form

    def clean(self):
        self.cleaned_data["password"] = self.cleaned_data.get("password", "") + self.cleaned_data.get("otp_token", "")
        return super().clean()
