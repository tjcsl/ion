from django import forms

from intranet.apps.groups.models import Group
from intranet.apps.users.models import User


class SendPushNotificationForm(forms.Form):
    title = forms.CharField(max_length=50)
    body = forms.CharField(
        max_length=200,
        widget=forms.Textarea(attrs={"rows": 4, "cols": 40}),
    )
    url = forms.URLField(initial="https://ion.tjhsst.edu")
    users = forms.ModelMultipleChoiceField(queryset=User.objects.all(), required=False)
    groups = forms.ModelMultipleChoiceField(queryset=Group.objects.all(), required=False)
