from django import forms

from ....groups.models import Group


class QuickGroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ["name"]


class GroupForm(forms.ModelForm):
    student_visible = forms.BooleanField(initial=False, required=False)

    class Meta:
        model = Group
        fields = ["name", "student_visible"]


class UploadGroupForm(forms.Form):
    file = forms.FileField()
