from django import forms

from ...models import EighthRoom


class RoomForm(forms.ModelForm):
    class Meta:
        model = EighthRoom
        fields = ["name", "capacity", "available_for_eighth"]
        widgets = {"capacity": forms.TextInput(attrs={"size": 4})}
