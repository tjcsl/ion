# -*- coding: utf-8 -*-

import logging

from django import forms
from django.contrib.auth.forms import AuthenticationForm

from six import iteritems

logger = logging.getLogger(__name__)


class AuthenticateForm(AuthenticationForm):

    """Implements a login form.

    Attributes:
        username
            The username text field.
        password
            The password text field.

    """
    username = forms.CharField(required=True, widget=forms.widgets.TextInput(attrs={"placeholder": "Username"}), error_messages={"required": "Invalid username", "inactive": "Access disallowed."})
    password = forms.CharField(required=True, widget=forms.widgets.PasswordInput(attrs={"placeholder": "Password"}), error_messages={"required": "Invalid password", "inactive": "Access disallowed."})

    def is_valid(self):
        """Validates the username and password in the form"""
        form = super(AuthenticateForm, self).is_valid()
        for f, error in iteritems(self.errors):
            if f != "__all__":
                self.fields[f].widget.attrs.update({"class": "error", "placeholder": ", ".join(list(error))})
            else:
                errors = list(error)
                if "This account is inactive." in errors:
                    message = "Permission denied: account restricted."
                else:
                    message = "Invalid password"
                self.fields["password"].widget.attrs.update({"class": "error", "placeholder": message})

        return form
