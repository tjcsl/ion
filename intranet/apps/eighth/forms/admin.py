from django import forms
from ..models import EighthActivity, EighthBlock


class BlockSelectionForm(forms.Form):
    block = forms.ModelChoiceField(queryset=EighthBlock.objects.all(), empty_label="Select a block")


class ActivitySelectionForm(forms.Form):
    def __init__(self, block=None, *args, **kwargs):
        super(ActivitySelectionForm, self).__init__(*args, **kwargs)

        if block is None:
            queryset = EighthActivity.objects.all()
        else:
            queryset = block.activities.all()

        self.fields["activity"] = forms.ModelChoiceField(queryset=queryset, empty_label="Select an activity")
