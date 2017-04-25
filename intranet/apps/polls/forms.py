# -*- coding: utf-8 -*-

import bleach

from django import forms

from .models import Poll


class PollForm(forms.ModelForm):

    def __init__(self, all_groups=False, *args, **kwargs):
        super(forms.ModelForm, self).__init__(*args, **kwargs)
        self.fields["description"].widget = forms.Textarea()

    def clean_description(self):
        desc = self.cleaned_data["description"]
        # SAFE HTML
        desc = bleach.linkify(desc)
        return desc

    class Meta:
        model = Poll
        exclude = []  # type: List[str]
