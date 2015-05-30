# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.core.validators import RegexValidator
from ...models import EighthBlock


block_letter_validator = RegexValidator(r"^[a-zA-Z]$", "Only single letters are allowed.")


class BlockSelectionForm(forms.Form):

    def __init__(self, label="Block", exclude_before_date=None, only_locked=False, *args, **kwargs):
        super(BlockSelectionForm, self).__init__(*args, **kwargs)

        filter_params = {}

        if exclude_before_date is not None:
            filter_params["date__gte"] = exclude_before_date

        if only_locked:
            filter_params["locked"] = True

        queryset = EighthBlock.objects.filter(**filter_params)

        self.fields["block"] = forms.ModelChoiceField(queryset=queryset,
                                                      label=label,
                                                      empty_label="Select a block")


class QuickBlockForm(forms.ModelForm):
    block_letter = forms.CharField(max_length=1, validators=[block_letter_validator])

    class Meta:
        model = EighthBlock
        fields = ["date", "block_letter"]


class BlockForm(forms.ModelForm):
    block_letter = forms.CharField(max_length=1, validators=[block_letter_validator])

    class Meta:
        model = EighthBlock
        fields = [
            "date",
            "block_letter",
            "locked",
            "override_blocks"
        ]
