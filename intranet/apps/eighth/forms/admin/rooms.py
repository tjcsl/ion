from django import forms

from ...models import EighthActivity, EighthRoom
from .activities import ActivityMultiDisplayField


class RoomForm(forms.ModelForm):
    activities = ActivityMultiDisplayField(queryset=None, required=False)

    class Meta:
        model = EighthRoom
        fields = ["name", "capacity", "available_for_eighth"]
        widgets = {"capacity": forms.TextInput(attrs={"size": 4})}

    def __init__(self, *args, label="Activities", **kwargs):  # pylint: disable=unused-argument
        super().__init__(*args, **kwargs)
        self.fields["activities"].queryset = EighthActivity.objects.exclude(deleted=True).all()
