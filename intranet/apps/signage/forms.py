from django import forms


class SetSignCustomSwitchTimeForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    action = forms.CharField(widget=forms.HiddenInput, initial="set_custom_switch_time_for_all_signs")
    time = forms.TimeField(
        widget=forms.TimeInput(format="%H:%M"),
        input_formats=("%H:%M",),
        help_text="Time at which to switch to the custom page for the Sign. Leave blank to clear. Example: 16:30",
        required=False,
    )
