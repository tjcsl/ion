# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from django import forms
from django.db.models import Q
from ....users.models import User
from ...models import EighthActivity, EighthScheduledActivity
logger = logging.getLogger(__name__)


class ActivityDisplayField(forms.ModelChoiceField):

    def label_from_instance(self, obj):
        return "{}: {}".format(obj.aid, obj.name)


class ActivityMultiDisplayField(forms.ModelMultipleChoiceField):

    def label_from_instance(self, obj):
        return "{}: {}".format(obj.aid, obj.name)


class ActivitySelectionForm(forms.Form):

    def __init__(self, label="Activity", block=None, sponsor=None, include_cancelled=False, *args, **kwargs):
        super(ActivitySelectionForm, self).__init__(*args, **kwargs)

        if block is not None:
            if sponsor is not None:
                sponsoring_filter = (Q(sponsors=sponsor) |
                                     (Q(sponsors=None) &
                                      Q(activity__sponsors=sponsor)))
                activity_ids = (EighthScheduledActivity.objects
                                                       .filter(block=block)
                                                       .filter(sponsoring_filter)
                                                       .values_list("activity__id", flat=True)
                                                       .nocache())
            else:
                activity_ids = (EighthScheduledActivity.objects
                                                       .exclude(activity__deleted=True)
                                                       .filter(block=block)
                                                       .values_list("activity__id", flat=True)
                                                       .nocache())
                if not include_cancelled:
                    activity_ids = activity_ids.exclude(cancelled=True)

            queryset = (EighthActivity.objects.filter(id__in=activity_ids)
                                              .order_by("name"))
        else:
            if sponsor is not None:
                queryset = (EighthActivity.undeleted_objects
                                          .filter(sponsors=sponsor)
                                          .order_by("name")).nocache()
            else:
                queryset = (EighthActivity.undeleted_objects
                                          .all()
                                          .order_by("name")).nocache()

        self.fields["activity"] = ActivityDisplayField(queryset=queryset,
                                                       label=label,
                                                       empty_label="Select an activity")


class QuickActivityForm(forms.ModelForm):

    class Meta:
        model = EighthActivity
        fields = ["name"]


class ActivityMultiSelectForm(forms.Form):
    activities = ActivityMultiDisplayField(queryset=None)

    def __init__(self, label="Activities", *args, **kwargs):
        super(ActivityMultiSelectForm, self).__init__(*args, **kwargs)
        self.fields["activities"].queryset = EighthActivity.objects.exclude(deleted=True).all()


class ScheduledActivityMultiSelectForm(forms.Form):
    activities = ActivityMultiDisplayField(queryset=None)

    def __init__(self, label="Activities", block=None, *args, **kwargs):
        super(ScheduledActivityMultiSelectForm, self).__init__(*args, **kwargs)
        logger.debug(block)
        if block is not None:
            activity_ids = (EighthScheduledActivity.objects
                                                   .exclude(activity__deleted=True)
                            #.exclude(cancelled=True)
                                                   .filter(block=block)
                                                   .values_list("activity__id", flat=True)
                                                   .nocache())
            queryset = (EighthActivity.objects.filter(id__in=activity_ids)
                                              .order_by("name"))
        else:
            queryset = (EighthActivity.undeleted_objects.all()
                                                        .order_by("name")
                                                        .nocache())

        logger.debug(queryset)
        self.fields["activities"].queryset = queryset


class ActivityForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ActivityForm, self).__init__(*args, **kwargs)

        for fieldname in ["sponsors", "rooms", "users_allowed", "groups_allowed"]:
            self.fields[fieldname].help_text = None

        # Simple way to filter out teachers without hitting LDAP. This
        # shouldn't be a problem unless the username scheme changes and
        # the consequences of error are not significant.

        # TODO: What we would like to do here (from users.forms):
        # self.fields["users_allowed"] = SortedUserMultipleChoiceField(queryset=User.objects.get_students())
        # HOWEVER: this will result in LDAP information being queried for *all 1800 users.*
        # We need a better way to accomplish this. The solution below works because it only prints
        # the username field which doesn't require an LDAP query to access.
        self.fields["users_allowed"].queryset = User.objects.get_students()

        self.fields["presign"].label = "48 Hour"

    class Meta:
        model = EighthActivity
        fields = [
            "name",
            "description",
            "sponsors",
            "rooms",
            "id",
            "presign",
            "one_a_day",
            "both_blocks",
            "sticky",
            "special",
            "administrative",
            "restricted",
            "users_allowed",
            "groups_allowed",
            "freshmen_allowed",
            "sophomores_allowed",
            "juniors_allowed",
            "seniors_allowed"
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5, "cols": 46}),
            "name": forms.TextInput(attrs={"style": "width: 292px"})
        }
