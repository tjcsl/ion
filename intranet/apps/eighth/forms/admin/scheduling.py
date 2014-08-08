# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from ...models import EighthScheduledActivity


class ScheduledActivityForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ScheduledActivityForm, self).__init__(*args, **kwargs)

        for fieldname in ["sponsors", "rooms"]:
            self.fields[fieldname].help_text = None

        for fieldname in ["block", "activity"]:
            self.fields[fieldname].widget = forms.HiddenInput()

    class Meta:
        model = EighthScheduledActivity
        fields = ["block", "activity", "rooms", "capacity", "sponsors", "comments"]
        widgets = {
            "capacity": forms.TextInput(),
            "comments": forms.Textarea(attrs={"rows": 2, "cols": 30})
        }
