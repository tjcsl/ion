from django.forms import ModelForm
from django import forms
from .models import Announcement


class AnnouncementForm(ModelForm):
    author = forms.CharField(max_length=63, widget=forms.HiddenInput())

    class Meta:
        model = Announcement
