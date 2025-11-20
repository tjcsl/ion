from django.forms import ModelForm

from .models import Day, DayType


class DayTypeForm(ModelForm):
    class Meta:
        model = DayType
        fields = ["name", "special", "codenames", "blocks"]


class DayForm(ModelForm):
    class Meta:
        model = Day
        fields = ["date", "day_type"]
