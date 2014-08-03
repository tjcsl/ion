from django import forms
from django.contrib.auth.models import Group


class QuickAddGroup(forms.ModelForm):
    class Meta:
        model = Group
        fields = ["name"]


class BlockForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ["name"]
