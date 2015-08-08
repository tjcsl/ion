from django import forms

class ProfileEditForm(forms.Form):
    """A form containing editable fields in the User model."""
    admin_comments = forms.CharField(label="Admin Comments", widget=forms.Textarea)

    student_id = forms.IntegerField(label="FCPS Student ID")
    first_name = forms.CharField(label="First Name")
    middle_name = forms.CharField(label="Middle Name")
    last_name = forms.CharField(label="Last Name")
    title = forms.CharField(label="Title")
    nickname = forms.CharField(label="Nickname")
    graduation_year = forms.IntegerField(label="Graduation Year")
    sex = forms.CharField(label="Sex (M or F)")
    birthday = forms.DateField(label="Birth Date")
    home_phone = forms.CharField(label="Home Phone")

    street = forms.CharField(label="Street")
    city = forms.CharField(label="City")
    state = forms.CharField(label="State")
    postal_code = forms.CharField(label="ZIP")
    counselor_id = forms.IntegerField(label="Counselor ID")
    #locker = forms.CharField(label="Locker")
    
    FIELDS = ["admin_comments",
              "student_id",
              "first_name",
              "middle_name",
              "last_name",
              "title",
              "nickname",
              "graduation_year",
              "sex",
              "birthday",
              "home_phone"]
    ADDRESS_FIELDS = ["street",
                       "city",
                       "state",
                       "postal_code"]

class UserChoiceField(forms.ModelChoiceField):
    """
    A ModelChoiceField that returns a user's full name instead
    of their TJ username (which is the default string representation).

    """

    def label_from_instance(self, obj):
        return obj.full_name

class SortedUserChoiceField(forms.ModelChoiceField):
    """
    A ModelChoiceField that returns a user's Last, First name instead
    of their TJ username (which is the default string representation).

    """

    def label_from_instance(self, obj):
        return obj.last_first


class UserMultipleChoiceField(forms.ModelMultipleChoiceField):
    """
    A ModelMultipleChoiceField that returns a user's full name instead
    of their TJ username (which is the default string representation).

    """

    def label_from_instance(self, obj):
        return obj.full_name

class SortedUserMultipleChoiceField(forms.ModelMultipleChoiceField):
    """
    A ModelMultipleChoiceField that returns a user's Last, First name instead
    of their TJ username (which is the default string representation).

    """

    def label_from_instance(self, obj):
        return obj.last_first
