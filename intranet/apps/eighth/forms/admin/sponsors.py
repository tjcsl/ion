from django import forms
from django.core.exceptions import ValidationError

from ...models import EighthSponsor
from ....users.models import User


class AutoCreateUserField(forms.ChoiceField):
    widget = forms.TextInput

    def clean(self, value):
        if value in self.empty_values:
            return None

        try:
            id_value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(self.error_messages["invalid_choice"], code="invalid_choice", params={"value": value})

        try:
            user = User.objects.get(id=id_value)
        except User.DoesNotExist:
            raise ValidationError(self.error_messages["invalid_choice"], code="invalid_choice", params={"value": value})

        return user


class SponsorForm(forms.ModelForm):
    user = AutoCreateUserField(label="User ID", required=False)

    class Meta:
        model = EighthSponsor
        fields = ["first_name", "last_name", "user", "department", "full_time", "online_attendance", "contracted_eighth", "show_full_name"]
