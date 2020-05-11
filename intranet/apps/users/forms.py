from django import forms
from django.contrib.auth import get_user_model

from .models import Address


class ProfileEditForm(forms.ModelForm):
    """A form containing editable fields in the User model."""

    GENDERS = ((True, "Male"), (False, "Female"))

    admin_comments = forms.CharField(label="Admin Comments", widget=forms.Textarea, required=False)
    student_id = forms.IntegerField(label="FCPS Student ID")
    first_name = forms.CharField(label="First Name")
    middle_name = forms.CharField(label="Middle Name", required=False)
    last_name = forms.CharField(label="Last Name")
    nickname = forms.CharField(label="Nickname", required=False)
    graduation_year = forms.IntegerField(label="Graduation Year")
    gender = forms.ChoiceField(choices=GENDERS, label="Sex (M or F)")
    counselor_id = forms.IntegerField(label="Counselor ID", required=False)

    class Meta:
        model = get_user_model()
        fields = ["admin_comments", "student_id", "first_name", "middle_name", "last_name", "title", "nickname", "graduation_year", "gender"]


class UserChoiceField(forms.ModelChoiceField):
    """A ModelChoiceField that returns a user's full name instead of their TJ username (which is the
    default string representation)."""

    def label_from_instance(self, obj):
        return obj.full_name


class SortedUserChoiceField(forms.ModelChoiceField):
    """A ModelChoiceField that returns a user's Last, First name instead of their TJ username (which
    is the default string representation)."""

    def label_from_instance(self, obj):
        return obj.last_first_id


class UserMultipleChoiceField(forms.ModelMultipleChoiceField):
    """A ModelMultipleChoiceField that returns a user's full name instead of their TJ username
    (which is the default string representation)."""

    def label_from_instance(self, obj):
        return obj.full_name


class SortedUserMultipleChoiceField(forms.ModelMultipleChoiceField):
    """A ModelMultipleChoiceField that returns a user's Last, First name instead of their TJ
    username (which is the default string representation)."""

    def label_from_instance(self, obj):
        return obj.last_first_id


class SortedTeacherMultipleChoiceField(forms.ModelMultipleChoiceField):
    """A ModelMultipleChoiceField that returns a user's Last, First initial instead of their TJ
    username (which is the default string representation)."""

    def __init__(self, *args, **kwargs):
        self.show_username = False
        if "show_username" in kwargs:
            self.show_username = kwargs["show_username"]
            del kwargs["show_username"]
        super(SortedTeacherMultipleChoiceField, self).__init__(*args, **kwargs)

    def label_from_instance(self, obj):
        name = obj.last_first_initial
        return "{} ({})".format(name, obj.username) if self.show_username else name


class AddressForm(forms.ModelForm):
    """Form for user address"""

    street = forms.CharField(label="Street")
    city = forms.CharField(label="City")
    state = forms.CharField(label="State")
    postal_code = forms.CharField(label="ZIP")

    class Meta:
        model = Address
        fields = ["street", "city", "state", "postal_code"]
