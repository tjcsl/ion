import logging
from django import forms
from ..users.models import Grade


logger = logging.getLogger(__name__)


class PersonalInformationForm(forms.Form):
    def __init__(self,
                 num_phones=1,
                 num_emails=1,
                 num_webpages=1,
                 *args, **kwargs):
        super(PersonalInformationForm, self).__init__(*args, **kwargs)

        self.num_phones = num_phones
        self.num_emails = num_emails
        self.num_webpages = num_webpages

        for i in range(num_phones):
            self.fields["other_phone_{}".format(i)] = forms.CharField(max_length=50, required=True, label="Other phone(s)")

        for i in range(num_emails):
            self.fields["email_{}".format(i)] = forms.EmailField(required=True, label="Email(s)")

        for i in range(num_webpages):
            self.fields["webpage_{}".format(i)] = forms.URLField(required=True, label="Webpage(s)")

    mobile_phone = forms.CharField(max_length=50, required=True, label="Mobile phone")
    home_phone = forms.CharField(max_length=50, required=True, label="Home phone")


class PreferredPictureForm(forms.Form):
    def __init__(self, user, *args, **kwargs):
        super(PreferredPictureForm, self).__init__(*args, **kwargs)
        self.PREFERRED_PICTURE_CHOICES = [
            ("default", "Auto-select the most recent photo"),
        ]

        photos = user.photo_permissions["self"]

        for i in range(4):
            grade = Grade.names[i]
            if photos[grade] is not None:
                self.PREFERRED_PICTURE_CHOICES += [(grade, grade.title() + " Photo")]



        self.fields["preferred_picture"] = forms.ChoiceField(choices=self.PREFERRED_PICTURE_CHOICES,
                                                             widget=forms.RadioSelect(),
                                                             required=True)


class PrivacyOptionsForm(forms.Form):
    def __init__(self, user, *args, **kwargs):
        super(PrivacyOptionsForm, self).__init__(*args, **kwargs)

        def flag(label, default):
            return forms.BooleanField(initial=default, label=label)

        self.fields["showaddress"] = flag(None, False)
        self.fields["showaddress-self"] = flag("Show Address", False)

        self.fields["showphone"] = flag(None, False)
        self.fields["showphone-self"] = flag("Show Phone", False)

        self.fields["showbirthday"] = flag(None, False)
        self.fields["showbirthday-self"] = flag("Show Birthday", False)

        pictures_label = "Show Pictures"
        if user.is_student:
            pictures_label += " on Import"
        self.fields["showpictures"] = flag(None, False)
        self.fields["showpictures-self"] = flag(pictures_label, False)

        self.fields["showschedule"] = flag(None, False)
        self.fields["showschedule-self"] = flag("Show Class Schedule", False)

        self.fields["showeighth"] = flag(None, False)
        self.fields["showeighth-self"] = flag("Show 8th Pd. Schedule", False)

        #self.fields["showlocker"] = flag(None, False)
        #self.fields["showlocker-self"] = flag("Show Locker", False)
