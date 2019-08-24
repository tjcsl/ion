from django import forms


class FeedbackForm(forms.Form):
    """A form for sending comments to the Intranet team."""

    comments = forms.CharField(label="Comments", max_length=50000, widget=forms.Textarea)
