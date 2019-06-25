from django import forms


class StartDateForm(forms.Form):
    date = forms.DateField()
