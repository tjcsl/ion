import logging
from typing import List  # noqa

from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q

from ...models import EighthActivity, EighthScheduledActivity

logger = logging.getLogger(__name__)


class ActivityDisplayField(forms.ModelChoiceField):

    cancelled_acts = None  # type: List[EighthActivity]

    def __init__(self, *args, **kwargs):
        if "block" in kwargs:
            block = kwargs.pop("block")
            self.cancelled_acts = [s.activity for s in EighthScheduledActivity.objects.filter(block=block, cancelled=True)]

        super(ActivityDisplayField, self).__init__(*args, **kwargs)

    def label_from_instance(self, obj):
        if self.cancelled_acts and obj in self.cancelled_acts:
            return "{}: {} (CANCELLED)".format(obj.aid, obj.name)

        return "{}: {}".format(obj.aid, obj.name)


class ActivityMultiDisplayField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return "{}: {}".format(obj.aid, obj.name)


class ActivitySelectionForm(forms.Form):
    def __init__(self, *args, label="Activity", block=None, sponsor=None, include_cancelled=False, **kwargs):
        super(ActivitySelectionForm, self).__init__(*args, **kwargs)

        if block is None:
            if sponsor is not None:
                queryset = EighthActivity.undeleted_objects.filter(sponsors=sponsor).order_by("name")
            else:
                queryset = EighthActivity.undeleted_objects.all().order_by("name")

            self.fields["activity"] = ActivityDisplayField(queryset=queryset, label=label, empty_label="Select an activity")
        else:
            if sponsor is not None:
                sponsoring_filter = Q(sponsors=sponsor) | (Q(sponsors=None) & Q(activity__sponsors=sponsor))
                activity_ids = EighthScheduledActivity.objects.filter(block=block).filter(sponsoring_filter).values_list("activity__id", flat=True)
            else:
                activity_ids = (
                    EighthScheduledActivity.objects.exclude(activity__deleted=True).filter(block=block).values_list("activity__id", flat=True)
                )
                if not include_cancelled:
                    activity_ids = activity_ids.exclude(cancelled=True)

            queryset = EighthActivity.objects.filter(id__in=activity_ids).order_by("name")

            self.fields["activity"] = ActivityDisplayField(queryset=queryset, label=label, empty_label="Select an activity", block=block)


class QuickActivityForm(forms.ModelForm):
    class Meta:
        model = EighthActivity
        fields = ["name"]


class ActivityMultiSelectForm(forms.Form):
    activities = ActivityMultiDisplayField(queryset=None)

    def __init__(self, *args, label="Activities", **kwargs):  # pylint: disable=unused-argument
        super(ActivityMultiSelectForm, self).__init__(*args, **kwargs)
        self.fields["activities"].queryset = EighthActivity.objects.exclude(deleted=True).all()


class ScheduledActivityMultiSelectForm(forms.Form):
    activities = ActivityMultiDisplayField(queryset=None)

    def __init__(self, *args, label="Activities", block=None, **kwargs):  # pylint: disable=unused-argument
        super(ScheduledActivityMultiSelectForm, self).__init__(*args, **kwargs)
        if block is not None:
            activity_ids = (
                EighthScheduledActivity.objects.exclude(activity__deleted=True)
                # .exclude(cancelled=True)
                .filter(block=block).values_list("activity__id", flat=True)
            )
            queryset = EighthActivity.objects.filter(id__in=activity_ids).order_by("name")
        else:
            queryset = EighthActivity.undeleted_objects.all().order_by("name")

        self.fields["activities"].queryset = queryset


class ActivityForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ActivityForm, self).__init__(*args, **kwargs)

        for fieldname in ["sponsors", "rooms", "users_allowed", "groups_allowed", "users_blacklisted"]:
            self.fields[fieldname].help_text = None

        # Simple way to filter out teachers without hitting LDAP. This
        # shouldn't be a problem unless the username scheme changes and
        # the consequences of error are not significant.

        # FIXME: TODO: What we would like to do here (from users.forms):
        # self.fields["users_allowed"] = SortedUserMultipleChoiceField(queryset=get_user_model().objects.get_students())
        # HOWEVER: this will result in LDAP information being queried for *all 1800 users.*
        # We need a better way to accomplish this. The solution below works because it only prints
        # the username field which doesn't require an LDAP query to access.
        student_objects = get_user_model().objects.get_students()
        self.fields["users_allowed"].queryset = student_objects
        self.fields["users_blacklisted"].queryset = student_objects

        self.fields["presign"].label = "48 Hour"
        self.fields["default_capacity"].help_text = "Overrides the sum of each room's capacity above, if set."

        # These fields are rendered on the right of the page on the edit activity page.
        self.right_fields = set(
            [
                "restricted",
                "users_allowed",
                "groups_allowed",
                "users_blacklisted",
                "freshmen_allowed",
                "sophomores_allowed",
                "juniors_allowed",
                "seniors_allowed",
            ]
        )

    class Meta:
        model = EighthActivity
        fields = [
            "name",
            "description",
            "sponsors",
            "rooms",
            "default_capacity",
            "id",
            "presign",
            "one_a_day",
            "both_blocks",
            "sticky",
            "special",
            "administrative",
            "finance",
            "restricted",
            "users_allowed",
            "groups_allowed",
            "users_blacklisted",
            "freshmen_allowed",
            "sophomores_allowed",
            "juniors_allowed",
            "seniors_allowed",
            "wed_a",
            "wed_b",
            "fri_a",
            "fri_b",
            "admin_comments",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 9, "cols": 46}),
            "name": forms.TextInput(attrs={"style": "width: 292px"}),
            "admin_comments": forms.Textarea(attrs={"rows": 5, "cols": 46}),
        }
