# -*- coding: utf-8 -*-

from django import forms


class DateRangeForm(forms.Form):
    start_date = forms.DateField()
    end_date = forms.DateField()
