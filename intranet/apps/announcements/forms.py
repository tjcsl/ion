# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from .models import Announcement, AnnouncementRequest
from ..users.models import User

class AnnouncementForm(forms.ModelForm):

    class Meta:
        model = Announcement
        fields = [
            "title",
            "author",
            "content",
            "groups"
        ]

class AnnouncementRequestForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(AnnouncementRequestForm, self).__init__(*args, **kwargs)
        self.fields["content"].help_text = "The text you wish to have in the announcement."
        self.fields["notes"].help_text = "Any information about this announcement you wish to "\
                                         "share with the Intranet administrators. You should include information "\
                                         "regarding group restrictions here."
        self.fields["teachers_requested"].help_text = "The teacher(s) who will approve your announcement."
        self.fields["teachers_requested"].queryset = (User.objects.get_teachers())

    class Meta:
        model = AnnouncementRequest
        fields = [
            "title",
            "content",
            "teachers_requested",
            "notes"
        ]

