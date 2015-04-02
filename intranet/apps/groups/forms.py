# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.contrib.auth.models import Group


class GroupForm(forms.ModelForm):

    class Meta:
        model = Group
        fields = ["name", "permissions"]
