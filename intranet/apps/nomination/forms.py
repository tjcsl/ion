# -*- coding: utf-8 -*-

from django import forms

from .models import NominationPosition


class CreateNominationPositionForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(CreateNominationPositionForm, self).__init__(*args, **kwargs)

    class Meta:
        model = NominationPosition
        fields = ["position_name"]
