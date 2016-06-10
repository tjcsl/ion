# -*- coding: utf-8 -*-
from django import forms
from .models import ParkingApplication, CarApplication


class ParkingApplicationForm(forms.ModelForm):
    class Meta:
        model = ParkingApplication
        fields = [
            "email",
            "mentorship"
        ]


class CarApplicationForm(forms.ModelForm):
    class Meta:
        model = CarApplication
        fields = [
            "license_plate",
            "make",
            "model",
            "year"
        ]
