# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from ....users.models import User
from ...models import EighthActivity


class ActivitySelectionForm(forms.Form):
    def __init__(self, block=None, label="Activity", *args, **kwargs):
        super(ActivitySelectionForm, self).__init__(*args, **kwargs)

        if block is None:
            queryset = EighthActivity.undeleted_objects.all()
        else:
            queryset = block.activities.all()

        self.fields["activity"] = forms.ModelChoiceField(queryset=queryset, label=label, empty_label="Select an activity")


class QuickActivityForm(forms.ModelForm):
    class Meta:
        model = EighthActivity
        fields = ["name"]


class ActivityForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ActivityForm, self).__init__(*args, **kwargs)

        for fieldname in ["sponsors", "rooms", "users_allowed", "groups_allowed"]:
            self.fields[fieldname].help_text = None

        # Simple way to filter out teachers without hitting LDAP
        # Warning: will break in approximately 1000 years or if the student
        # username format ever changes
        self.fields["users_allowed"].queryset = User.objects \
                                                    .filter(username__startswith="2")

        self.fields["presign"].label = "48 Hour"

    class Meta:
        model = EighthActivity
        exclude = ["deleted"]
        widgets = {
            "description": forms.TextInput()
        }
