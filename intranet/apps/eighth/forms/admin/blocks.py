from django import forms
from django.core.validators import RegexValidator
from ...models import EighthBlock


block_letter_validator = RegexValidator(r"^[a-zA-Z]$", "Only single letters are allowed.")


class BlockSelectionForm(forms.Form):
    block = forms.ModelChoiceField(queryset=EighthBlock.objects.all(), empty_label="Select a block")


class QuickBlockForm(forms.ModelForm):
    block_letter = forms.CharField(max_length=1, validators=[block_letter_validator])

    class Meta:
        model = EighthBlock
        fields = ["date"]


class BlockForm(forms.ModelForm):
    block_letter = forms.CharField(max_length=1, validators=[block_letter_validator])

    class Meta:
        model = EighthBlock
        exclude = ["activities"]
