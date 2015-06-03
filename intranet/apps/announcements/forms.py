# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from .models import Announcement, AnnouncementRequest


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
    #teachers_requested = forms.MultipleChoiceField(help_text="The faculty member(s) who will approve the announcement.")
    class Meta:
        model = AnnouncementRequest
        fields = [
            "title",
            "content",
            "notes",
            "teachers_requested"
        ]