from django import forms
from django.core.validators import RegexValidator

from ...models import EighthBlock, EighthScheduledActivity

block_letter_validator = RegexValidator(
    r"^[a-z A-Z0-9_-]{1,10}$", "A block letter must be less than 10 characters long, and include only alphanumeric characters and spaces."
)


class BlockDisplayField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.id}: {obj}"


class BlockSelectionForm(forms.Form):
    def __init__(self, *args, label="Block", exclude_before_date=None, only_locked=False, **kwargs):
        super().__init__(*args, **kwargs)

        filter_params = {}

        if exclude_before_date is not None:
            filter_params["date__gte"] = exclude_before_date

        if only_locked:
            filter_params["locked"] = True

        queryset = EighthBlock.objects.filter(**filter_params)

        self.fields["block"] = BlockDisplayField(queryset=queryset, label=label, empty_label="Select a block")


class HybridBlockSelectionForm(forms.Form):
    def __init__(self, *args, label="Block", exclude_before_date=None, only_locked=False, **kwargs):
        super().__init__(*args, **kwargs)

        filter_params = {}

        if exclude_before_date is not None:
            filter_params["date__gte"] = exclude_before_date

        if only_locked:
            filter_params["locked"] = True

        blocks_set = set()
        for b in EighthBlock.objects.filter(**filter_params).filter(
            eighthscheduledactivity__in=EighthScheduledActivity.objects.filter(activity__name="z - Hybrid Sticky")
        ):
            blocks_set.add((str(b.date), b.block_letter[0]))
        queryset = [(b, f"{b[0]} ({b[1]})") for b in sorted(blocks_set)]
        queryset.append(("", "Select or search for a block"))

        self.fields["block"] = forms.ChoiceField(choices=queryset, label=label)


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
