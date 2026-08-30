from django import forms

from ..users.models import Email


class SeniorEmailForwardForm(forms.Form):
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)

        label = "Email Forward"
        self.fields["email"] = forms.ModelChoiceField(
            queryset=Email.objects.filter(user=user, verified=True), required=False, label=label, disabled=(user.emails.all().count() == 0)
        )
