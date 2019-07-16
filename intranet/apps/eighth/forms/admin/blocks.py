from django import forms
from django.core.validators import RegexValidator

from ...models import EighthBlock

block_letter_validator = RegexValidator(
    r"^[a-z A-Z0-9_-]{1,10}$", "A block letter must be less than 10 characters long, and include only alphanumeric characters and spaces."
)


class BlockDisplayField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return "{}: {}".format(obj.id, str(obj))


class BlockSelectionForm(forms.Form):
    def __init__(self, *args, label="Block", exclude_before_date=None, only_locked=False, **kwargs):
        super(BlockSelectionForm, self).__init__(*args, **kwargs)

        filter_params = {}

        if exclude_before_date is not None:
            filter_params["date__gte"] = exclude_before_date

        if only_locked:
            filter_params["locked"] = True

        queryset = EighthBlock.objects.filter(**filter_params)

        self.fields["block"] = BlockDisplayField(queryset=queryset, label=label, empty_label="Select a block")


class QuickBlockForm(forms.ModelForm):
    block_letter = forms.CharField(max_length=10, validators=[block_letter_validator])

    class Meta:
        model = EighthBlock
        fields = ["date", "block_letter"]


class BlockForm(forms.ModelForm):
    block_letter = forms.CharField(max_length=10, validators=[block_letter_validator])

    class Meta:
        model = EighthBlock
        fields = [
            "date",
            "block_letter",
            "locked",
            # "override_blocks",
            "signup_time",
            "comments",
        ]
