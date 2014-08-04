# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from ...models import EighthRoom


class RoomForm(forms.ModelForm):
    class Meta:
        model = EighthRoom
        fields = ["name", "capacity"]
        widgets = {
            "capacity": forms.TextInput()
        }
