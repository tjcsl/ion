from django import forms
from ...models import EighthBlock


class BlockSelectionForm(forms.Form):
    block = forms.ModelChoiceField(queryset=EighthBlock.objects.all(), empty_label="Select a block")
