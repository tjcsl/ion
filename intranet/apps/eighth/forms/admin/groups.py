# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from ....groups.models import Group


class QuickGroupForm(forms.ModelForm):

    class Meta:
        model = Group
        fields = ["name"]


class GroupForm(forms.ModelForm):

    class Meta:
        model = Group
        fields = ["name"]

class UploadGroupForm(forms.Form):
    file = forms.FileField()