# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from collections import OrderedDict

from django.db.models import Count

from rest_framework import serializers
from rest_framework.reverse import reverse

from .models import (EighthActivity, EighthBlock, EighthScheduledActivity,
                     EighthSignup, EighthSponsor)
from ..users.models import User

logger = logging.getLogger(__name__)


class EighthActivityListSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="api_eighth_activity_detail")

    class Meta:
        model = EighthActivity
        fields = ("id",
                  "url",
                  "name")


class EighthActivityDetailSerializer(serializers.HyperlinkedModelSerializer):
    scheduled_on = serializers.SerializerMethodField("fetch_scheduled_on")

    def fetch_scheduled_on(self, act):
        scheduled_on = OrderedDict()
        scheduled_activities = EighthScheduledActivity.objects.filter(activity=act).select_related("block").order_by("block__date")

        # user = self.context.get("user", self.context["request"].user)
        # favorited_activities = set(user.favorited_activity_set
        #                               .values_list("id", flat=True))
        # available_restricted_acts = EighthActivity.restricted_activities_available_to_user(user)

        for scheduled_activity in scheduled_activities:
            scheduled_on[scheduled_activity.block.id] = {
                "id": scheduled_activity.block.id,
                "date": scheduled_activity.block.date,
                "block_letter": scheduled_activity.block.block_letter,
                "url": reverse("api_eighth_block_detail",
                               args=[scheduled_activity.block.id],
                               request=self.context["request"]),
                "roster": {
                    "id": scheduled_activity.id,
                    "url": reverse("api_eighth_scheduled_activity_signup_list",
                                   args=[scheduled_activity.id],
                                   request=self.context["request"]),
                }
            }
        logger.debug(scheduled_on)
        return scheduled_on

    class Meta:
        model = EighthActivity
        fields = ("id",
                  "name",
                  "description",
                  "administrative",
                  "restricted",
                  "presign",
                  "one_a_day",
                  "both_blocks",
                  "sticky",
                  "special",
                  "scheduled_on")


class EighthBlockListSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="api_eighth_block_detail")

    class Meta:
        model = EighthBlock
        fields = ("id",
                  "url",
                  "date",
                  "block_letter",
                  "locked")


class EighthBlockDetailSerializer(serializers.Serializer):
    id = serializers.ReadOnlyField()
    activities = serializers.SerializerMethodField("fetch_activity_list_with_metadata")
    date = serializers.DateField()
    block_letter = serializers.CharField(max_length=10)
    comments = serializers.CharField(max_length=100)

    def process_scheduled_activity(self, scheduled_activity, request=None, user=None, favorited_activities=None, available_restricted_acts=None):
        activity = scheduled_activity.activity
        restricted_for_user = (activity.restricted and
                               not (user.is_eighth_admin and not user.is_student) and
                               (activity.id not in available_restricted_acts))
        prefix = "Special: " if activity.special else ""
        prefix += activity.name
        if scheduled_activity.title:
            prefix += " - " + scheduled_activity.title
        middle = " (R)" if restricted_for_user else ""
        suffix = " (S)" if activity.sticky else ""
        suffix += " (BB)" if activity.both_blocks else ""
        suffix += " (A)" if activity.administrative else ""
        suffix += " (Deleted)" if activity.deleted else ""

        name_with_flags = prefix + middle + suffix
        name_with_flags_for_user = prefix + (middle if restricted_for_user else "") + suffix

        activity_info = {
            "id": activity.id,
            "aid": activity.aid,
            "scheduled_activity": {
                "id": scheduled_activity.id,
                "url": reverse("api_eighth_scheduled_activity_signup_list",
                               args=[scheduled_activity.id],
                               request=request)
            },
            "url": reverse("api_eighth_activity_detail",
                           args=[activity.id],
                           request=request),
            "name": activity.name,
            "name_with_flags": name_with_flags,
            "name_with_flags_for_user": name_with_flags_for_user,
            "description": activity.description,
            "cancelled": scheduled_activity.cancelled,
            "favorited": activity.id in favorited_activities,
            "roster": {
                "count": 0,
                "capacity": 0,
                "url": reverse("api_eighth_scheduled_activity_signup_list",
                               args=[scheduled_activity.id],
                               request=request)
            },
            "rooms": [],
            "sponsors": [],
            "restricted": activity.restricted,
            "restricted_for_user": restricted_for_user,
            "both_blocks": activity.both_blocks,
            "one_a_day": activity.one_a_day,
            "special": scheduled_activity.get_special(),
            "administrative": activity.administrative,
            "presign": activity.presign,
            "sticky": activity.sticky,
            "title": scheduled_activity.title,
            "comments": scheduled_activity.comments,
            "display_text": ""
        }
        return activity_info

    def fetch_activity_list_with_metadata(self, block):
        activity_list = {}
        scheduled_activity_to_activity_map = {}

        # Find all scheduled activities that don't correspond to
        # deleted activities
        scheduled_activities = (block.eighthscheduledactivity_set
                                     .exclude(activity__deleted=True)
                                     .select_related("activity"))

        user = self.context.get("user", self.context["request"].user)
        favorited_activities = set(user.favorited_activity_set
                                       .values_list("id", flat=True))
        available_restricted_acts = EighthActivity.restricted_activities_available_to_user(user)

        for scheduled_activity in scheduled_activities:
            activity_info = self.process_scheduled_activity(scheduled_activity,
                                                            self.context["request"],
                                                            user,
                                                            favorited_activities,
                                                            available_restricted_acts)
            activity = scheduled_activity.activity
            scheduled_activity_to_activity_map[scheduled_activity.id] = activity.id
            activity_list[activity.id] = activity_info

        # Find the number of students signed up for every activity
        # in this block
        activities_with_signups = (EighthSignup.objects
                                               .filter(scheduled_activity__block=block)
                                               .exclude(scheduled_activity__activity__deleted=True)
                                               .values_list("scheduled_activity__activity_id")
                                               .annotate(user_count=Count("scheduled_activity")))

        for activity, user_count in activities_with_signups:
            activity_list[activity]["roster"]["count"] = user_count

        sponsors_dict = (EighthSponsor.objects
                                      .values_list("id",
                                                   "user_id",
                                                   "first_name",
                                                   "last_name",
                                                   "show_full_name"))

        all_sponsors = dict((sponsor[0],
                             {"user_id": sponsor[1],
                              "name": sponsor[2] + " " + sponsor[3] if sponsor[4] else sponsor[3]}) for sponsor in sponsors_dict)

        activity_ids = scheduled_activities.values_list("activity__id")
        sponsorships = (EighthActivity.sponsors
                                      .through
                                      .objects
                                      .filter(eighthactivity_id__in=activity_ids)
                                      .select_related("sponsors")
                                      .values("eighthactivity", "eighthsponsor"))

        scheduled_activity_ids = scheduled_activities.values_list("id", flat=True)
        overidden_sponsorships = (EighthScheduledActivity.sponsors.through.objects
                                                         .filter(eighthscheduledactivity_id__in=scheduled_activity_ids)
                                                         .values("eighthscheduledactivity", "eighthsponsor"))

        for sponsorship in sponsorships:
            activity_id = int(sponsorship["eighthactivity"])
            sponsor_id = sponsorship["eighthsponsor"]
            sponsor = all_sponsors[sponsor_id]

            if sponsor["user_id"]:
                # We're not using User.get_user() here since we only want
                # a value from LDAP that is probably already cached.
                # This eliminates several hundred SQL queries on some
                # pages.
                dn = User.dn_from_id(sponsor["user_id"])
                if dn is not None:
                    name = User(dn=dn).last_name
                else:
                    name = None
            else:
                name = None

            activity_list[activity_id]["sponsors"].append(sponsor["name"] or name)

        activities_sponsors_overidden = []
        for sponsorship in overidden_sponsorships:
            scheduled_activity_id = sponsorship["eighthscheduledactivity"]
            activity_id = scheduled_activity_to_activity_map[scheduled_activity_id]
            sponsor_id = sponsorship["eighthsponsor"]
            sponsor = all_sponsors[sponsor_id]

            if activity_id not in activities_sponsors_overidden:
                activities_sponsors_overidden.append(activity_id)
                del activity_list[activity_id]["sponsors"][:]

            if sponsor["user_id"]:
                # See a few lines up for why we're not using User.get_user()
                dn = User.dn_from_id(sponsor["user_id"])
                if dn is not None:
                    name = User(dn=dn).last_name
                else:
                    name = None
            else:
                name = None
            activity_list[activity_id]["sponsors"].append(sponsor["name"] or name)

        roomings = (EighthActivity.rooms.through.objects
                                  .filter(eighthactivity_id__in=activity_ids)
                                  .select_related("eighthroom", "eighthactivity"))
        overidden_roomings = (EighthScheduledActivity.rooms
                                                     .through
                                                     .objects
                                                     .filter(eighthscheduledactivity_id__in=scheduled_activity_ids)
                                                     .select_related("eighthroom", "eighthscheduledactivity"))

        for rooming in roomings:
            activity_id = rooming.eighthactivity.id
            activity_cap = rooming.eighthactivity.default_capacity
            room_name = rooming.eighthroom.name
            activity_list[activity_id]["rooms"].append(room_name)
            if activity_cap:
                # use activity default capacity instead of sum of activity rooms
                activity_list[activity_id]["roster"]["capacity"] = activity_cap
            else:
                activity_list[activity_id]["roster"]["capacity"] += rooming.eighthroom.capacity

        activities_rooms_overidden = []
        for rooming in overidden_roomings:
            scheduled_activity_id = rooming.eighthscheduledactivity.id

            activity_id = scheduled_activity_to_activity_map[scheduled_activity_id]
            if activity_id not in activities_rooms_overidden:
                activities_rooms_overidden.append(activity_id)
                del activity_list[activity_id]["rooms"][:]
                activity_list[activity_id]["roster"]["capacity"] = 0
            room_name = rooming.eighthroom.name
            activity_list[activity_id]["rooms"].append(room_name)
            activity_list[activity_id]["roster"]["capacity"] += rooming.eighthroom.capacity

        for scheduled_activity in scheduled_activities:
            if scheduled_activity.capacity is not None:
                capacity = scheduled_activity.capacity
                sched_act_id = scheduled_activity.activity.id
                activity_list[sched_act_id]["roster"]["capacity"] = capacity

        return activity_list

    class Meta:
        fields = ("id",
                  "activities",
                  "date",
                  "block_letter")


class EighthSignupSerializer(serializers.ModelSerializer):
    block = serializers.SerializerMethodField("block_info")
    activity = serializers.SerializerMethodField("activity_info")
    scheduled_activity = serializers.SerializerMethodField("scheduled_activity_info")

    def block_info(self, signup):
        return {
            "id": signup.scheduled_activity.block.id,
            "date": signup.scheduled_activity.block.date,
            "url": reverse("api_eighth_block_detail",
                           args=[signup.scheduled_activity.block.id],
                           request=self.context["request"])
        }

    def activity_info(self, signup):
        return {
            "id": signup.scheduled_activity.activity.id,
            "title": signup.scheduled_activity.title_with_flags,
            "url": reverse("api_eighth_activity_detail",
                           args=[signup.scheduled_activity.activity.id],
                           request=self.context["request"])
        }

    def scheduled_activity_info(self, signup):
        return signup.scheduled_activity.id

    class Meta:
        model = EighthSignup
        fields = ("id",
                  "block",
                  "activity",
                  "scheduled_activity",
                  "user")


class UserSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    def get_url(self, user):
        return reverse("api_user_profile_detail",
                       args=[user.id],
                       request=self.context["request"])

    class Meta:
        model = User
        fields = ("id",
                  "full_name",
                  "username",
                  "url")


class EighthScheduledActivitySerializer(serializers.ModelSerializer):
    block = serializers.SerializerMethodField("block_info")
    activity = serializers.SerializerMethodField("activity_info")
    signups = serializers.SerializerMethodField("signups_info")
    name = serializers.SerializerMethodField()
    capacity = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super(EighthScheduledActivitySerializer, self).__init__(*args, **kwargs)
        logger.debug(kwargs)
        if "context" in kwargs and "request" in kwargs["context"]:
            self.request = kwargs["context"]["request"]
        else:
            self.request = None

    def get_name(self, scheduled_activity):
        return scheduled_activity.title_with_flags

    def get_capacity(self, scheduled_activity):
        return scheduled_activity.get_true_capacity()

    def block_info(self, scheduled_activity):
        return {
            "id": scheduled_activity.block.id,
            "date": scheduled_activity.block.date,
            "url": reverse("api_eighth_block_detail",
                           args=[scheduled_activity.block.id],
                           request=self.context["request"])
        }

    def activity_info(self, scheduled_activity):
        return {
            "id": scheduled_activity.activity.id,
            "title": scheduled_activity.title_with_flags,
            "url": reverse("api_eighth_activity_detail",
                           args=[scheduled_activity.activity.id],
                           request=self.context["request"])
        }

    def signups_info(self, scheduled_activity):
        signups = scheduled_activity.members

        if self.request:
            signups = scheduled_activity.get_viewable_members_serializer(self.request)

        serializer = UserSerializer(signups, context=self.context, many=True)
        return {
            "members": serializer.data,
            "count": scheduled_activity.members.count(),
            "viewable_count": signups.count()
        }

    def num_signups(self, scheduled_activity):
        return scheduled_activity.members.count()

    class Meta:
        model = EighthScheduledActivity
        fields = ("id",
                  "name",
                  "block",
                  "activity",
                  "signups",
                  "capacity")


def add_signup_validator(value):
    if 'scheduled_activity' in value:
        return
    if 'block' in value and 'activity' in value and not value.get('use_scheduled_activity', False):
        return
    raise serializers.ValidationError('Either scheduled_activity, or block and activity must exist. use_scheduled_activity must be false to use block and activity.')


class EighthAddSignupSerializer(serializers.Serializer):
    block = serializers.PrimaryKeyRelatedField(queryset=EighthBlock.objects.all(), required=False)
    activity = serializers.PrimaryKeyRelatedField(queryset=EighthActivity.objects.all(), required=False)
    scheduled_activity = serializers.PrimaryKeyRelatedField(queryset=EighthScheduledActivity.objects.select_related('activity').select_related('block'), required=False)
    use_scheduled_activity = serializers.BooleanField(required=False)
    force = serializers.BooleanField(required=False)

    class Meta:
        validators = [add_signup_validator]
