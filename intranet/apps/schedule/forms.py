# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.forms import ModelForm
from .models import Day, DayType

class DayTypeForm(ModelForm):

    class Meta:
        model = DayType
        fields = [
            "name",
            "special",
            "codenames",
            "blocks"
        ]

class DayForm(ModelForm):

    class Meta:
        model = Day
        fields = [
            "date",
            "type"
        ]