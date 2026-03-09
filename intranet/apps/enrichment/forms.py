import datetime  # for mass form

from django import forms

from .models import EnrichmentActivity


class EnrichmentActivityForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["presign"].label = "2 day pre-signup"

    class Meta:
        model = EnrichmentActivity

        fields = ["title", "description", "time", "location", "capacity", "presign", "groups_allowed", "groups_blacklisted"]


WEEKDAY_FIELDS = [
    ("monday", "Monday"),
    ("tuesday", "Tuesday"),
    ("wednesday", "Wednesday"),
    ("thursday", "Thursday"),
    ("friday", "Friday"),
]


class EnrichmentActivityBulkForm(EnrichmentActivityForm):
    """
    A way to create multiple enrichment activities at once.
    A user would check off boxes given a date in the selected week.
    """

    week_of = forms.DateField(
        label="Target Week",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    monday = forms.BooleanField(label="Monday", required=False)
    tuesday = forms.BooleanField(label="Tuesday", required=False)
    wednesday = forms.BooleanField(label="Wednesday", required=False)
    thursday = forms.BooleanField(label="Thursday", required=False)
    friday = forms.BooleanField(label="Friday", required=False)
    activity_time = forms.TimeField(label="Time of day", widget=forms.TimeInput(attrs={"type": "time"}), initial=datetime.time(12, 0))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # remove time so it doesn't appear in the form
        self.fields.pop("time")

    def clean(self):
        cleaned = super().clean()
        # Require at least one day to be checked
        days_checked = any(cleaned.get(day) for day, _ in WEEKDAY_FIELDS)
        if not days_checked:
            raise forms.ValidationError("Please select at least one day of the week.")
        return cleaned

    def get_selected_dates(self):  # returns in the form of a list.
        week_of = self.cleaned_data["week_of"]
        activity_time = self.cleaned_data["activity_time"]
        monday = week_of - datetime.timedelta(days=week_of.weekday())
        offsets = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
        }
        return [
            datetime.datetime.combine(monday + datetime.timedelta(days=offset), activity_time)
            for day_name, offset in offsets.items()
            if self.cleaned_data.get(day_name)
        ]
