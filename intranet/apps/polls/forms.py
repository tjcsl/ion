from django import forms

from ...utils.html import safe_html
from .models import Poll


class PollForm(forms.ModelForm):
    def clean_description(self):
        desc = self.cleaned_data["description"]
        # SAFE HTML
        desc = safe_html(desc)
        return desc

    class Meta:
        model = Poll
        fields = ["title", "description", "start_time", "end_time", "visible", "is_secret", "is_election", "groups"]
        widgets = {"description": forms.Textarea()}
        labels = {"is_secret": "Secret", "is_election": "Election"}
        help_texts = {
            "is_secret": "This will prevent Ion administrators from viewing individual users' votes.",
            "is_election": "Enable election formatting and results features.",
        }
