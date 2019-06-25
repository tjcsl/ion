from django import forms
from django.utils import timezone

from .models import Event
from ..groups.models import Group


class EventForm(forms.ModelForm):
    def __init__(self, *args, all_groups=False, **kwargs):
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
        fields = [
            "title", "description", "time", "location", "groups", "show_attending",
            "show_on_dashboard", "public", "category", "open_to",
        ]


class AdminEventForm(forms.ModelForm):
    def __init__(self, *args, all_groups=False, **kwargs):
        super(AdminEventForm, self).__init__(*args, **kwargs)
        if not all_groups:
            self.fields["groups"].queryset = Group.objects.student_visible()

    class Meta:
        model = Event
        fields = [
            "title", "description", "time", "location", "scheduled_activity", "announcement",
            "groups", "show_attending", "show_on_dashboard", "public", "category", "open_to",
        ]
        widgets = {"scheduled_activity": forms.NumberInput(), "announcement": forms.NumberInput()}
        help_texts = {
            "scheduled_activity": "OPTIONAL: Enter the ID of the scheduled activity -- it will be displayed above the event.",
            "announcement": "OPTIONAL: Enter the ID of the announcement -- it will be displayed above the event.",
        }
