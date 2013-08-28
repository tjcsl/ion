from django.forms import ModelForm
from django import forms
from .models import Announcement


class AnnouncementForm(ModelForm):

    class Meta:
        model = Announcement
