from django import forms
from ...models import EighthBlock


class BlockSelectionForm(forms.Form):
    block = forms.ModelChoiceField(queryset=EighthBlock.objects.all(), empty_label="Select a block")


class QuickAddBlockForm(forms.ModelForm):
    class Meta:
        model = EighthBlock
        fields = ["date", "block_letter"]


class BlockForm(forms.ModelForm):
    class Meta:
        model = EighthBlock
        exclude = ["activities"]
