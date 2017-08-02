# -*- coding: utf-8 -*-
import logging

from django import forms

from ..users.models import User, Grade, Phone, Email, Website

logger = logging.getLogger(__name__)


class PreferredPictureForm(forms.Form):

    def __init__(self, user, *args, **kwargs):
        super(PreferredPictureForm, self).__init__(*args, **kwargs)

        self.PREFERRED_PICTURE_CHOICES = [("AUTO", "Auto-select the most recent photo")]

        for i in range(4):
            try:
                grade = Grade.names[i]
                user.photos.get(grade=grade)  # Only display option if the photo exists
                self.PREFERRED_PICTURE_CHOICES += [(grade, grade.title() + " Photo")]
            except:
                pass

        self.fields["preferred_photo"] = forms.ChoiceField(choices=self.PREFERRED_PICTURE_CHOICES,
                                                           widget=forms.RadioSelect(),
                                                           required=True)


class PrivacyOptionsForm(forms.Form):

    def __init__(self, user, *args, **kwargs):
        super(PrivacyOptionsForm, self).__init__(*args, **kwargs)

        def flag(label, default):
            return forms.BooleanField(initial=default, label=label, required=False)

        self.fields["showaddress"] = flag(None, False)
        self.fields["showaddress-self"] = flag("Show Address", False)

        self.fields["showtelephone"] = flag(None, False)
        self.fields["showtelephone-self"] = flag("Show Phone", False)

        self.fields["showbirthday"] = flag(None, False)
        self.fields["showbirthday-self"] = flag("Show Birthday", False)

        pictures_label = "Show Pictures"
        if user.is_student:
            pictures_label += " on Import"
        self.fields["showpictures"] = flag(None, False)
        self.fields["showpictures-self"] = flag(pictures_label, False)

        # photos = user.photo_permissions["self"]

        # for i in range(4):
        #     grade = Grade.names[i]
        #     if photos[grade] is not None:
        #         self.fields["photoperm-{}".format(grade)] = flag(None, False)
        #         self.fields["photoperm-{}-self".format(grade)] = flag("Show {} Photo".format(grade.capitalize()), False)

        self.fields["showschedule"] = flag(None, False)
        self.fields["showschedule-self"] = flag("Show Class Schedule", False)

        self.fields["showeighth"] = flag(None, False)
        self.fields["showeighth-self"] = flag("Show Eighth Period Schedule", False)

        # self.fields["showlocker"] = flag(None, False)
        # self.fields["showlocker-self"] = flag("Show Locker", False)

        if not user.has_admin_permission("preferences"):
            for name in self.fields:
                if not name.endswith("-self"):
                    self.fields[name].widget.attrs['class'] = 'disabled'


class NotificationOptionsForm(forms.Form):

    def __init__(self, user, *args, **kwargs):
        super(NotificationOptionsForm, self).__init__(*args, **kwargs)

        def flag(label, default):
            return forms.BooleanField(initial=default, label=label, required=False)

        self.fields["receive_news_emails"] = flag("Receive News Emails", False)
        self.fields["receive_eighth_emails"] = flag("Receive Eighth Period Emails", False)


class PhoneForm(forms.ModelForm):

    """Represents a phone number (number + purpose)"""
    class Meta:
        model = Phone
        fields = ['purpose', 'number']


class EmailForm(forms.ModelForm):

    class Meta:
        model = Email
        fields = ['address']


class WebsiteForm(forms.ModelForm):

    class Meta:
        model = Website
        fields = ['url']

PhoneFormset = forms.inlineformset_factory(User, Phone, form=PhoneForm, extra=1)
EmailFormset = forms.inlineformset_factory(User, Email, form=EmailForm, extra=1)
WebsiteFormset = forms.inlineformset_factory(User, Website, form=WebsiteForm, extra=1)
