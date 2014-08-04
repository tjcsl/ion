# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from ...models import EighthSponsor


class SponsorForm(forms.ModelForm):
    class Meta:
        model = EighthSponsor
        widgets = {
            "user": forms.TextInput()
        }
        labels = {
            "user": "User ID:"
        }
