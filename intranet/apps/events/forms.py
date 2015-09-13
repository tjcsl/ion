# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from .models import Event
from ..groups.models import Group
from ..users.models import User


class EventForm(forms.ModelForm):

    def __init__(self, all_groups=False, *args, **kwargs):
        super(forms.ModelForm, self).__init__(*args, **kwargs)
        if not all_groups:
            self.fields["groups"].queryset = Group.objects.student_visible()

    class Meta:
        model = Event
        exclude = ["created_time",
                   "last_modified_time",
                   "user",
                   "scheduled_activity",
                   "announcement",
                   "attending",
                   "links",
                   "approved",
                   "rejected",
                   "approved_by",
                   "rejected_by"]
