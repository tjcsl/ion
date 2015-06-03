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

    class Meta:
        model = AnnouncementRequest
        fields = [
            "title",
            "content",
            "notes",
            "teachers_requested"
        ]
