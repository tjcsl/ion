from django.db import forms
from .models import LostItem, FoundItem, CalculatorRegistration, ComputerRegistration, PhoneRegistration

class LostItemForm(forms.Form):
    class Meta:
        model = LostItem
        fields = [
            "title",
            "description",
            "last_seen"
        ]


class FoundItemForm(forms.Form):
    class Meta:
        model = FoundItem
        fields = [
            "title",
            "description",
            "found"
        ]


class CalculatorRegistrationForm(forms.Form):
    class Meta:
        model = CalculatorRegistration
        fields = [
            "calc_type",
            "calc_serial",
            "calc_id"
        ]


class ComputerRegistrationForm(forms.Form):
    class Meta:
        model = ComputerRegistration
        fields = [
            "manufacturer",
            "model",
            "serial",
            "description"
        ]


class PhoneRegistrationForm(forms.Form):
    class Meta:
        model = PhoneRegistration
        fields = [
            "manufacturer",
            "model",
            "serial",
            "description"
        ]


