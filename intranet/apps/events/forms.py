# -*- coding: utf-8 -*-

from django import forms
from django.utils import timezone

from .models import Event
from ..groups.models import Group


class EventForm(forms.ModelForm):

    def __init__(self, all_groups=False, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
        if not all_groups:
            self.fields["groups"].queryset = Group.objects.student_visible()

    def clean_time(self):
        time = self.cleaned_data["time"]
        if time < timezone.now():
            raise forms.ValidationError("The event time cannot be in the past!")
        return time

    class Meta:
        model = Event
        exclude = [
            "added", "updated", "user", "scheduled_activity", "announcement", "attending", "links", "approved", "rejected", "approved_by",
            "rejected_by"
        ]


class AdminEventForm(forms.ModelForm):

    def __init__(self, all_groups=False, *args, **kwargs):
        super(AdminEventForm, self).__init__(*args, **kwargs)
        if not all_groups:
            self.fields["groups"].queryset = Group.objects.student_visible()
        self.fields["scheduled_activity"].widget = forms.NumberInput()
        self.fields["scheduled_activity"].help_text = "OPTIONAL: Enter the ID of the scheduled activity -- it will be displayed above the event."
        self.fields["announcement"].widget = forms.NumberInput()
        self.fields["announcement"].help_text = "OPTIONAL: Enter the ID of the announcement -- it will be displayed above the event."

    class Meta:
        model = Event
        exclude = ["added", "updated", "user", "attending", "links", "approved", "rejected", "approved_by", "rejected_by"]
