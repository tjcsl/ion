# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.forms import ModelForm
from .models import DayType

class DayTypeForm(ModelForm):

    class Meta:
        model = DayType
        fields = [
            "name",
            "special",
            "codenames",
            "blocks"
        ]
