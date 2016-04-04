from django import forms
from django.core import validators
from django.utils.encoding import force_text

class PhoneField(forms.Field):
    widget = forms.TextInput
    default_error_messages = {
        'incomplete': 'Enter a phone number.',
        'invalid': 'Please enter a valid phone number.'
    }
    def __init__(self, max_length=None, *args, **kwargs):
        self.max_length = max_length
        super(PhoneField, self).__init__(
        *args, **kwargs)
        self.validators.append(validators.RegexValidator(r'^[0-9]+$', 'Please enter a valid phone number.'))
        if max_length is not None:
            self.validators.append(validators.MaxLengthValidator(int(max_length)))

    def to_python(self, value):
        "Returns a Unicode object."
        if value in self.empty_values:
            return ''
        value = force_text(value)
        if self.strip:
            value = value.strip()
        return value

    def widget_attrs(self, widget):
        attrs = super(PhoneField, self).widget_attrs(widget)
        if self.max_length is not None:
            attrs.update({'maxlength': str(self.max_length)})
        return attrs

