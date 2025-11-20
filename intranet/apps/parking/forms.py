from django import forms

from .models import CarApplication, ParkingApplication


class ParkingApplicationForm(forms.ModelForm):
    class Meta:
        model = ParkingApplication
        fields = ["email", "mentorship"]


class CarApplicationForm(forms.ModelForm):
    class Meta:
        model = CarApplication
        fields = ["license_plate", "make", "model", "year"]
