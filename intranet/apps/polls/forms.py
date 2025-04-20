from django import forms

from ...utils.html import safe_html
from .models import Poll


class PollForm(forms.ModelForm):
    send_notification = forms.BooleanField(
        initial=True,
        required=False,
        help_text="This will send a notification to eligible students asking them to vote in this poll",
        label="Send notification",
    )

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

    # We need to make sure the send_notification field doesn't look out of place on the form
    field_order = Meta.fields[:4] + ["send_notification"] + Meta.fields[4:]
