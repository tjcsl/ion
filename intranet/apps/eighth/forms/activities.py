from typing import List  # noqa

from django import forms
from django.contrib.auth import get_user_model

from ..models import EighthActivity


class ActivitySettingsForm(forms.ModelForm):
    def __init__(self, *args, sponsors=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["officers"].queryset = get_user_model().objects.get_students()
        self.fields["club_sponsors"].queryset = get_user_model().objects.filter(user_type__in=["teacher", "counselor"])

        self.fields["subscriptions_enabled"].label = "Enable club announcements"
        self.fields["subscriptions_enabled"].help_text = "Allow students to subscribe to receive announcements for this activity through Ion."
        self.fields["club_sponsors"].label = "Teacher moderators"

        sponsors_list = "; ".join([str(sponsor) for sponsor in sponsors]) if sponsors else "no sponsors"

        self.fields["club_sponsors"].help_text = (
            f"Teacher moderators can post and manage this club's announcements. "
            f"These are in addition to the activity's eighth period sponsors ({sponsors_list})."
        )

        self.fields["officers"].label = "Student officers"
        self.fields["officers"].help_text = "Student officers can send club announcements to subscribers."

    class Meta:
        model = EighthActivity
        fields = [
            "subscriptions_enabled",
            "club_sponsors",
            "officers",
        ]
