from django import forms

from .models import SeniorEmailForward


class SeniorEmailForwardForm(forms.ModelForm):
    class Meta:
        model = SeniorEmailForward
        fields = ["email"]
