from django import forms
from ...models import EighthRoom


class RoomForm(forms.ModelForm):
    class Meta:
        model = EighthRoom
        fields = ["name", "capacity"]
