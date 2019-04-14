# -*- coding: utf-8 -*-
import logging

from django import forms

from ..users.models import User, Grade, Phone, Email, Website
from ..bus.models import Route

logger = logging.getLogger(__name__)


class BusRouteForm(forms.Form):

    def __init__(self, user, *args, **kwargs):
        super(BusRouteForm, self).__init__(*args, **kwargs)
        self.BUS_ROUTE_CHOICES = [(None, "Set bus route...")]
        routes = Route.objects.all()
        for route in routes:
            self.BUS_ROUTE_CHOICES += [(route.route_name, route.route_name)]
        self.fields['bus_route'] = forms.ChoiceField(choices=self.BUS_ROUTE_CHOICES, widget=forms.Select, required=False)


class PreferredPictureForm(forms.Form):

    def __init__(self, user, *args, **kwargs):
        super(PreferredPictureForm, self).__init__(*args, **kwargs)

        self.PREFERRED_PICTURE_CHOICES = [("AUTO", "Auto-select the most recent photo")]

        for i in range(4):
            try:
                grade = Grade.names[i]
                user.photos.get(grade_number=(i + 9))  # Only display option if the photo exists
                self.PREFERRED_PICTURE_CHOICES += [(i + 9, grade.title() + " Photo")]
            except Exception:
                pass

        self.fields["preferred_photo"] = forms.ChoiceField(choices=self.PREFERRED_PICTURE_CHOICES, widget=forms.RadioSelect(), required=True)


class PrivacyOptionsForm(forms.Form):

    def __init__(self, user, *args, **kwargs):
        super(PrivacyOptionsForm, self).__init__(*args, **kwargs)

        def flag(label, default):
            return forms.BooleanField(initial=default, label=label, required=False)

        self.fields["show_address"] = flag(None, False)
        self.fields["show_address-self"] = flag("Show Address", False)

        self.fields["show_telephone"] = flag(None, False)
        self.fields["show_telephone-self"] = flag("Show Phone", False)

        self.fields["show_birthday"] = flag(None, False)
        self.fields["show_birthday-self"] = flag("Show Birthday", False)

        pictures_label = "Show Pictures"
        if user.is_student:
            pictures_label += " on Import"
        self.fields["show_pictures"] = flag(None, False)
        self.fields["show_pictures-self"] = flag(pictures_label, False)

        # photos = user.photo_permissions["self"]

        # for i in range(4):
        #     grade = Grade.names[i]
        #     if photos[grade] is not None:
        #         self.fields["photoperm-{}".format(grade)] = flag(None, False)
        #         self.fields["photoperm-{}-self".format(grade)] = flag("Show {} Photo".format(grade.capitalize()), False)
        self.fields["show_eighth"] = flag(None, False)
        self.fields["show_eighth-self"] = flag("Show Eighth Period Schedule", False)

        self.fields["show_schedule"] = flag(None, False)
        self.fields["show_schedule-self"] = flag("Show Class Schedule", False)

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
        label = "Primary Email"
        if user.emails.all().count() == 0:
            label = "You can set a primary email after adding emails below."
        self.fields["primary_email"] = forms.ModelChoiceField(
            queryset=Email.objects.filter(user=user), required=False, label=label, disabled=(user.emails.all().count() == 0))


class PhoneForm(forms.ModelForm):
    """Represents a phone number (number + purpose)"""
    _number = forms.CharField(max_length=14)

    class Meta:
        model = Phone
        fields = ['purpose', '_number']


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
