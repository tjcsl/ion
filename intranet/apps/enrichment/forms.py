from django import forms

from .models import EnrichmentActivity


class EnrichmentActivityForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["presign"].label = "2 day pre-signup"

    class Meta:
        model = EnrichmentActivity

        fields = ["title", "description", "time", "location", "capacity", "presign", "groups_allowed", "groups_blacklisted"]
