import logging

from django import forms
from django.conf import settings

from .models import PrintJob

logger = logging.getLogger(__name__)


class PrintJobForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        printers = None
        if "printers" in kwargs:
            printers = kwargs["printers"]
            del kwargs["printers"]

        super().__init__(*args, **kwargs)

        if printers:
            self.fields["printer"].choices = [("", "Select a printer...")] + [(printer, desc) for printer, (desc, alerts) in printers.items()]

    def validate_size(self):
        filesize = self.file.__sizeof__()
        if filesize > settings.FILES_MAX_UPLOAD_SIZE:
            raise forms.ValidationError(f"The file uploaded is above the maximum upload size ({settings.FILES_MAX_UPLOAD_SIZE / 1024 / 1024}MB). ")

    def validate_page_range(self):
        """
        Expects string that only includes commas, digits, and dashes (already validated by regex)
        Validates that the page_range field's ranges and numbers correctly selects any pages from 1 to infinity.
        """
        # Return if user specifies all pages.
        if self.strip() == "":
            return

        # Gets number with suffix for clean error handling, e.g 1st, 2nd, 3rd
        def get_number_ordinal(n: int) -> str:
            if 11 <= (n % 100) <= 20:
                suffix = "th"
            else:
                # Codespell thinks 'nd' is misspelled
                suffix = ["th", "st", "nd", "rd", "th"][min(n % 10, 4)]  # codespell:ignore
            return str(n) + suffix

        range_list = [r.strip() for r in self.split(",")]
        prev_max = 0
        page_set = set()
        for i, single_range in enumerate(range_list, start=1):
            # Present a clean error message if there's multiple items or or not.
            error_prefix = "Input is invalid, " if len(range_list) == 1 else f"The {get_number_ordinal(i)} item is invalid, "

            if "-" in single_range:  # Handling a range.
                input_range = single_range.split("-")
                if len(input_range) != 2:
                    raise forms.ValidationError(error_prefix + "make sure the range is properly formatted (x-y).")

                try:
                    range_from, range_to = map(int, input_range)
                except ValueError as e:
                    raise forms.ValidationError(error_prefix + "you must specify two numbers around a dash for ranges.") from e

                if range_from <= 0 or range_to <= 0:
                    raise forms.ValidationError(error_prefix + "pages are numbered starting at 1, not 0.")

                if range_from > range_to:
                    raise forms.ValidationError(error_prefix + "the lower bound should be smaller than the upper bound.")

                if range_to < prev_max:
                    raise forms.ValidationError(
                        error_prefix + "please make sure your ranges and page numbers are in ascending order and not duplicating."
                    )  # LPR won't accept non ascending ranges.

                for page in range(range_from, range_to + 1):
                    if page in page_set:
                        raise forms.ValidationError(
                            error_prefix + "you may not specify duplicate page numbers."
                        )  # CUPS will ignore duplicating page numbers, user should be notified.
                    else:
                        page_set.add(page)

                prev_max = range_to
            else:  # Handling a single number.
                try:
                    page_num = int(single_range)
                except ValueError as e:
                    raise forms.ValidationError(error_prefix + "you may only specify numbers.") from e

                if page_num == 0:
                    raise forms.ValidationError(error_prefix + "pages are numbered starting at 1, not 0.")

                if page_num < prev_max:
                    raise forms.ValidationError(
                        error_prefix + "please make sure your ranges and page numbers are in ascending order and not duplicating."
                    )  # LPR won't accept non ascending ranges.

                if page_num in page_set:
                    raise forms.ValidationError(
                        error_prefix + "you may not specify duplicate page numbers."
                    )  # CUPS will ignore duplicating page numbers, user should be notified.
                else:
                    page_set.add(page_num)

                prev_max = page_num

        return

    file = forms.FileField(validators=[validate_size])
    printer = forms.ChoiceField()
    page_range = forms.RegexField(
        max_length=100,
        required=False,
        regex=r"^[0-9,\- ]*$",
        error_messages={"invalid": "This field must contain only a list of comma separated numbers and/or ranges separated by dashes."},
        help_text=(
            "Specify pages to print as a comma-separated list of ascending numbers and ranges (inclusive), e.g. '1-3, 5, 7'."
            "<br>You may not specify a page to print multiple times."
            "<br>Leave blank for all pages."
        ),
        validators=[validate_page_range],
        widget=forms.TextInput(attrs={"placeholder": "All Pages"}),
    )

    class Meta:
        model = PrintJob
        fields = ["file", "printer", "page_range", "duplex", "fit"]
