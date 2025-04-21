import logging

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model

from ..eighth.models import EighthActivity
from ..users.forms import SortedTeacherMultipleChoiceField
from .models import Announcement, AnnouncementRequest

logger = logging.getLogger(__name__)


class AnnouncementForm(forms.ModelForm):
    """A form for generating an announcement."""

    expiration_date = forms.DateTimeInput()
    notify_email_all = forms.BooleanField(required=False, label="Send Email to All")
    update_added_date = forms.BooleanField(required=False, label="Update Added Date")

    class Meta:
        model = Announcement
        fields = ["title", "author", "content", "groups", "expiration_date", "notify_post", "notify_email_all", "update_added_date", "pinned"]
        help_texts = {
            "expiration_date": "By default, announcements expire after two weeks. Choose the shortest time necessary.",
            "notify_post": "If this box is checked, students who have signed up for notifications will receive an email.",
            "notify_email_all": (
                "This will send an email notification to all of the users who can see this post. "
                "This option does NOT take users' email notification preferences into account, so please use with care."
            ),
            "update_added_date": (
                "If this announcement has already been added, update the added date to now so that the announcement is pushed to the top. "
                "If this option is not selected, the announcement will stay in its current position."
            ),
        }


class ClubAnnouncementForm(forms.ModelForm):
    """A form for posting a club announcement."""

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if user.is_announcements_admin:
            self.fields["activity"].queryset = EighthActivity.objects.filter(subscriptions_enabled=True)
        elif user.is_club_officer:
            self.fields["activity"].queryset = EighthActivity.objects.filter(subscriptions_enabled=True, officers=user)
        elif user.is_club_sponsor:
            self.fields["activity"].queryset = user.club_sponsor_for_set.filter(subscriptions_enabled=True)
        else:
            self.fields["activity"].queryset = []
        self.fields["activity"].required = True
        self.fields[
            "notify_post"
        ].help_text = "If this box is checked, students who have subscribed to your club's announcements will receive an email."

        if "instance" in kwargs:  # Don't allow changing the activity once the announcement has been created
            self.fields["activity"].widget.attrs["disabled"] = True
            self.fields["activity"].initial = kwargs["instance"].activity

    expiration_date = forms.DateTimeInput()
    notify_post = forms.BooleanField(required=False, initial=True)

    class Meta:
        model = Announcement
        fields = ["activity", "title", "content", "expiration_date", "notify_post", "public"]
        help_texts = {
            "expiration_date": "By default, announcements expire after two weeks. Choose the shortest time necessary.",
        }


class ClubAnnouncementEditForm(forms.ModelForm):
    """A form for editing a club announcement."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    expiration_date = forms.DateTimeInput()

    class Meta:
        model = Announcement
        fields = ["title", "content", "expiration_date", "public"]
        help_texts = {
            "expiration_date": "By default, announcements expire after two weeks. Choose the shortest time necessary.",
        }


class AnnouncementEditForm(forms.ModelForm):
    """A form for generating an announcement."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["expiration_date"].help_text = "By default, announcements expire after two weeks. Choose the shortest time necessary."

        self.fields["notify_post_resend"].help_text = "If this box is checked, students who have signed up for notifications will receive an email."

        self.fields["notify_email_all_resend"].help_text = (
            "This will resend an email notification to all of the users who can see this post. This option "
            "does NOT take users' email notification preferences into account, so please use with care."
        )

        self.fields["update_added_date"].help_text = (
            "If this announcement has already been added, update the added date to now so that the "
            "announcement is pushed to the top. If this option is not selected, the announcement will stay in "
            "its current position."
        )

    expiration_date = forms.DateTimeInput()
    notify_post_resend = forms.BooleanField(required=False, label="Resend notification")
    notify_email_all_resend = forms.BooleanField(required=False, label="Resend email to all users")
    update_added_date = forms.BooleanField(required=False, label="Update Added Date")

    class Meta:
        model = Announcement
        fields = ["title", "author", "content", "groups", "expiration_date", "update_added_date", "pinned"]


class AnnouncementRequestForm(forms.ModelForm):
    """A form for generating an announcement request."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].help_text = "The title of the announcement that will appear on Intranet."
        self.fields["author"].help_text = (
            "If you want this post to have a custom author entry, such as "
            '"Basket Weaving Club" or "TJ Faculty," enter that name here. '
            "Otherwise, your name will appear in this field automatically."
        )
        self.fields["content"].help_text = "The contents of the news post which will appear on Intranet."
        self.fields["expiration_date"].help_text = "By default, announcements expire after two weeks. Choose the shortest time necessary."
        self.fields["notes"].help_text = (
            "Any information about this announcement you wish to share with the Intranet "
            "administrators and teachers selected above. If you want to restrict this posting "
            f"to a specific group of students, such as the Class of {settings.SENIOR_GRADUATION_YEAR}, enter that request here."
        )
        self.fields["teachers_requested"] = SortedTeacherMultipleChoiceField(
            queryset=get_user_model().objects.get_approve_announcements_users_sorted(), show_username=True
        )
        self.fields["teachers_requested"].label = "Sponsor"
        self.fields["teachers_requested"].help_text = (
            "The teacher(s) who will approve your announcement. They will be sent an email "
            "with instructions on how to approve this post. Please do not select more than "
            "one or two."
        )

    class Meta:
        model = AnnouncementRequest
        fields = ["title", "author", "content", "expiration_date", "teachers_requested", "notes"]


class AnnouncementAdminForm(forms.Form):
    """A form for allowing admin to edit notifications on requests."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["notify_post"].help_text = "If this box is checked, students who have signed up for notifications will receive an email."
        self.fields["notify_email_all"].help_text = (
            "This will send an email notification to all of the users who can see this post. This option "
            "does NOT take users' email notification preferences into account, so please use with care."
        )

    notify_post = forms.BooleanField(required=False, initial=True)
    notify_email_all = forms.BooleanField(required=False, label="Send Email to All")
