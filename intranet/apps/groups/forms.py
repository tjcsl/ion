from django import forms
from django.contrib.auth.models import Group


class GroupForm(forms.ModelForm):

    class Meta:
        model = Group
