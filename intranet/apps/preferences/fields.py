from django import forms
from django.core import validators
from django.db import models
from django.utils.encoding import force_text


class PhoneField(models.Field):
    """Model field for a phone number"""

    def __init__(self, *args, **kwargs):
        kwargs["max_length"] = 17
        super(PhoneField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(PhoneField, self).deconstruct()
        del kwargs["max_length"]
        return name, path, args, kwargs

    def get_internal_type(self):
        return "CharField"

    def formfield(self, **kwargs):  # pylint: disable=arguments-differ
        # This is a fairly standard way to set up some defaults
        # while letting the caller override them.
        defaults = {"form_class": PhoneFormField}
        defaults.update(kwargs)
        return super(PhoneField, self).formfield(**defaults)


class PhoneFormField(forms.Field):
    widget = forms.TextInput
    default_error_messages = {"incomplete": "Please enter a phone number.", "invalid": "Please enter a valid phone number."}

    def __init__(self, *args, **kwargs):
        super(PhoneFormField, self).__init__(*args, **kwargs)
        self.validators.append(validators.RegexValidator(r"^[\dA-Z]{3}-?[\dA-Z]{3}-?[\dA-Z]{4}$", "Please enter a valid phone number."))

    def to_python(self, value):
        """Returns a Unicode object."""
        if value in self.empty_values:
            return ""
        value = force_text(value).strip()
        return value

    @staticmethod
    def prepare_value(value):
        return "" if value == "None" else value

    @staticmethod
    def widget_attrs(_):
        # Max phone number is 15, and US numbers can start with +1, so max length is 17
        return {"maxlength": "17"}
