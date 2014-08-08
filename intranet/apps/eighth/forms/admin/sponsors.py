# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.core.exceptions import ValidationError
from ....users.models import User
from ...models import EighthSponsor


class AutoCreateUserField(forms.ChoiceField):
    widget = forms.TextInput

    def clean(self, value):
        value = self.to_python(value)
        self.validate(value)
        if value in self.empty_values:
            return

        try:
            id_value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(
                self.error_messages["invalid_choice"],
                code="invalid_choice",
                params={"value": value}
            )

        try:
            user = User.objects.get(id=id_value)
        except User.DoesNotExist:
            try:
                user = User.get_user(id=id_value)
            except User.DoesNotExist:
                raise ValidationError(
                    self.error_messages["invalid_choice"],
                    code="invalid_choice",
                    params={"value": value}
                )
            user.username = user.ion_username
            user.set_unusable_password()
            user.save()

        return user


class SponsorForm(forms.ModelForm):
    user = AutoCreateUserField(required=False)

    class Meta:
        model = EighthSponsor
        labels = {
            "user": "User ID:"
        }
