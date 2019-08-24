from django import forms

from .models import Senior


class SeniorForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SeniorForm, self).__init__(*args, **kwargs)
        self.fields["college"].help_text = "CollegeBoard CEEB numbers are in parentheses."
        self.fields["college"].empty_label = "Undecided"
        self.fields["college_sure"].label = "Sure?"
        self.fields["college_sure"].help_text = "If you don't check this box, this school will be shown as unsure."
        self.fields["major_sure"].label = "Sure?"
        self.fields["major_sure"].help_text = "If you don't check this box, this major will be shown as unsure."

    class Meta:
        model = Senior
        fields = ["college", "college_sure", "major", "major_sure"]
