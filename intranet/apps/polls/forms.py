
from typing import List  # noqa

from django import forms

from .models import Poll

from ...utils.html import safe_html


class PollForm(forms.ModelForm):

    def __init__(self, all_groups=False, *args, **kwargs):
        super(PollForm, self).__init__(*args, **kwargs)
        self.fields["description"].widget = forms.Textarea()

    def clean_description(self):
        desc = self.cleaned_data["description"]
        # SAFE HTML
        desc = safe_html(desc)
        return desc

    class Meta:
        model = Poll
        exclude = []  # type: List[str]
