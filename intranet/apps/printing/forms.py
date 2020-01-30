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

        super(PrintJobForm, self).__init__(*args, **kwargs)

        if printers:
            self.fields["printer"].choices = [("", "Select a printer...")] + list(printers.items())

    def validate_size(self):
        filesize = self.file.__sizeof__()
        if filesize > settings.FILES_MAX_UPLOAD_SIZE:
            raise forms.ValidationError(
                "The file uploaded is above the maximum upload size ({}MB). ".format(settings.FILES_MAX_UPLOAD_SIZE / 1024 / 1024)
            )

    file = forms.FileField(validators=[validate_size])
    printer = forms.ChoiceField()
    page_range = forms.RegexField(
        max_length=100,
        required=False,
        regex=r"^[0-9,\- ]*$",
        error_messages={"invalid": "This field must contain only numbers or ranges of numbers."},
        widget=forms.TextInput(attrs={"placeholder": "All Pages"}),
    )

    class Meta:
        model = PrintJob
        fields = ["file", "printer", "page_range", "duplex", "fit"]
