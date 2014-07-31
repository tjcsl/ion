from django import forms
from ..models import EighthActivity, EighthBlock


class BlockSelectionForm(forms.Form):
    block = forms.ModelChoiceField(queryset=EighthBlock.objects.all(), empty_label="Select a block")


class ActivitySelectionForm(forms.Form):
    activity = forms.ModelChoiceField(queryset=EighthActivity.objects.all(), empty_label="Select an activity")


class BlockFilteredActivitySelectionForm(ActivitySelectionForm):
    def __init__(self, block=None, **kwargs):
        if block is not None:
            self.activity = forms.ModelChoiceField(queryset=block.activities.all(), empty_label="Select an activity")
        super(BlockFilteredActivitySelectionForm, self).__init__(**kwargs)
