# -*- coding: utf-8 -*-

from django import forms

from ...models import EighthRoom


class RoomSelectionForm(forms.Form):

    def __init__(self, block=None, label="Room", *args, **kwargs):
        super(RoomSelectionForm, self).__init__(*args, **kwargs)
        queryset = EighthRoom.objects.all()

        self.fields["room"] = forms.ModelChoiceField(queryset=queryset, label=label, empty_label="Select a room")


class RoomForm(forms.ModelForm):

    class Meta:
        model = EighthRoom
        fields = ["name", "capacity"]
        widgets = {"capacity": forms.TextInput(attrs={'size': 4})}
