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

    content = forms.CharField(help_text="The text you wish to have in the announcement.", widget=forms.Textarea)
    notes = forms.CharField(help_text="Any information about this announcement you wish to "\
                                      "share with the Intranet administrators. You should include information "\
                                      "regarding group restrictions here.", widget=forms.Textarea)
    
    def __init__(self, *args, **kwargs):
        super(AnnouncementRequestForm, self).__init__(*args, **kwargs)

        self.fields["teachers_requested"].queryset = (User.objects
                                                          .exclude(username__startswith="2"))

    class Meta:
        model = AnnouncementRequest
        fields = [
            "title",
            "content",
            "notes",
            "teachers_requested"
        ]