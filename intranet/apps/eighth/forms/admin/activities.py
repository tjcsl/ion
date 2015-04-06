# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.db.models import Q
from ....users.models import User
from ...models import EighthActivity, EighthScheduledActivity


class ActivitySelectionForm(forms.Form):

    def __init__(self, label="Activity", block=None, sponsor=None, *args, **kwargs):
        super(ActivitySelectionForm, self).__init__(*args, **kwargs)

        if block is not None:
            if sponsor is not None:
                sponsoring_filter = (Q(sponsors=sponsor) |
                                     (Q(sponsors=None) &
                                      Q(activity__sponsors=sponsor)))
                activity_ids = (EighthScheduledActivity.objects
                                                       .filter(block=block)
                                                       .filter(sponsoring_filter)
                                                       .values_list("activity__id", flat=True))
            else:
                activity_ids = (EighthScheduledActivity.objects
                                                       .exclude(activity__deleted=True)
                                                       .exclude(cancelled=True)
                                                       .filter(block=block)
                                                       .values_list("activity__id", flat=True))
            queryset = EighthActivity.objects.filter(id__in=activity_ids)
        else:
            if sponsor is not None:
                queryset = (EighthActivity.undeleted_objects
                                          .filter(sponsors=sponsor))
            else:
                queryset = EighthActivity.undeleted_objects.all()

        self.fields["activity"] = forms.ModelChoiceField(queryset=queryset,
                                                         label=label,
                                                         empty_label="Select an activity")


class QuickActivityForm(forms.ModelForm):

    class Meta:
        model = EighthActivity
        fields = ["name"]


class ActivityForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ActivityForm, self).__init__(*args, **kwargs)

        for fieldname in ["sponsors", "rooms", "users_allowed", "groups_allowed"]:
            self.fields[fieldname].help_text = None

        # Simple way to filter out teachers without hitting LDAP This
        # shouldn't be a problem unless TJ hires a teacher who loves
        # math so much that their name starts with the number 2. Even if
        # that does happen the consequences are not significant.
        self.fields["users_allowed"].queryset = (User.objects
                                                     .filter(username__startswith="2"))

        self.fields["presign"].label = "48 Hour"

    class Meta:
        model = EighthActivity
        fields = [
            "name",
            "description",
            "sponsors",
            "rooms",
            "presign",
            "one_a_day",
            "both_blocks",
            "sticky",
            "special",
            "restricted",
            "users_allowed",
            "groups_allowed",
            "freshmen_allowed",
            "sophomores_allowed",
            "juniors_allowed",
            "seniors_allowed"
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5, "cols": 46})
        }
