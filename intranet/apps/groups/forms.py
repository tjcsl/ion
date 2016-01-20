# -*- coding: utf-8 -*-

from django import forms

from .models import Group


class GroupForm(forms.ModelForm):

    class Meta:
        model = Group
        fields = ["name", "permissions"]
