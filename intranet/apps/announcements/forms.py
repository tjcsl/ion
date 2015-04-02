# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.forms import ModelForm
from .models import Announcement


class AnnouncementForm(ModelForm):
    class Meta:
        model = Announcement
        fields = [
            "title",
            "author",
            "content"
        ]
