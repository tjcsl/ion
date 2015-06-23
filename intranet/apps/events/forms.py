# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from .models import Event
from ..users.models import User


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            "title",
            "description",
            "location",
            "scheduled_activity",
            "announcement",
            "links",
            "groups"
        ]
