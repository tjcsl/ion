# -*- coding: utf-8 -*-

from django import forms


class StartDateForm(forms.Form):
    date = forms.DateField()
