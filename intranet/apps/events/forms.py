# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from .models import Event
from ..users.models import User


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        exclude = ["created_time",
                   "last_modified_time",
                   "user",
                   "scheduled_activity",
                   "announcement",
                   "attending"]
