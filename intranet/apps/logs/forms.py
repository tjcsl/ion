from django import forms


class FlagRequestForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    action = forms.CharField(widget=forms.HiddenInput, initial="flag_requests")
    flag = forms.CharField(max_length=255, required=True, help_text="Flag the selected requests for review by assigning them a label.")
