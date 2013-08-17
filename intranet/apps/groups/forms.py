from django.forms import ModelForm
from django import forms
from .models import Group


class GroupForm(ModelForm):

    class Meta:
        model = Group
