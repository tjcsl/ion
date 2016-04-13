from django import forms
from .models import LostItem, FoundItem


class LostItemForm(forms.ModelForm):

    class Meta:
        model = LostItem
        fields = [
            "title",
            "description",
            "last_seen",
            "found"
        ]


class FoundItemForm(forms.ModelForm):

    class Meta:
        model = FoundItem
        fields = [
            "title",
            "description",
            "found",
            "retrieved"
        ]

