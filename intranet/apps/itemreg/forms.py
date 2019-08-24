from django import forms

from .models import CalculatorRegistration, ComputerRegistration, PhoneRegistration


class CalculatorRegistrationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CalculatorRegistrationForm, self).__init__(*args, **kwargs)
        self.fields["calc_type"].label = "Calculator Type"
        self.fields["calc_serial"].label = "Calculator Serial"
        self.fields["calc_serial"].help_text = "Enter the calculator serial code (found engraved on the back of the calculator)"
        self.fields["calc_id"].label = "Calculator ID"
        self.fields["calc_id"].help_text = "Enter the calculator ID (without dashes)"

    class Meta:
        model = CalculatorRegistration
        fields = ["calc_type", "calc_serial", "calc_id"]


class ComputerRegistrationForm(forms.ModelForm):
    class Meta:
        model = ComputerRegistration
        fields = ["manufacturer", "model", "screen_size", "serial", "description"]


class PhoneRegistrationForm(forms.ModelForm):
    class Meta:
        model = PhoneRegistration
        fields = ["manufacturer", "model", "serial", "description"]
