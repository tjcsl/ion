# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from django.db.models import Count
from rest_framework import serializers
from rest_framework.reverse import reverse
from ..users.models import User
from .models import (
    EighthBlock, EighthActivity, EighthSignup,
    EighthSponsor, EighthScheduledActivity)


logger = logging.getLogger(__name__)


class EighthActivityDetailSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = EighthActivity
        fields = ("id",
                  "url",
                  "name",
                  "description",
                  "restricted",
                  "presign",
                  "one_a_day",
                  "both_blocks",
                  "sticky",
                  "special")


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
    id = serializers.Field()
    activities = serializers.SerializerMethodField("fetch_activity_list_with_metadata")
    date = serializers.DateField()
    block_letter = serializers.CharField(max_length=1)

    def fetch_activity_list_with_metadata(self, block):
        activity_list = {}
        scheduled_activity_to_activity_map = {}

        scheduled_activities = block.eighthscheduledactivity_set \
                                    .all() \
                                    .select_related("activity")
        for scheduled_activity in scheduled_activities:
            activity_info = {
                "id": scheduled_activity.activity.id,
                "scheduled_activity": scheduled_activity.id,
                "url": reverse("api_eighth_activity_detail",
                               args=[scheduled_activity.activity.id],
                               request=self.context["request"]),
                "name": scheduled_activity.activity.name,
                "description": scheduled_activity.activity.description,
                "roster": {
                    "count": 0,
                    "capacity": 0,
                    "url": reverse("api_eighth_scheduled_activity_signup_list",
                                   args=[scheduled_activity.id],
                                   request=self.context["request"])
                },
                "rooms": [],
                "sponsors": []
            }
            scheduled_activity_to_activity_map[scheduled_activity.id] = \
                scheduled_activity.activity.id

            activity_list[scheduled_activity.activity.id] = \
                activity_info

        activities = EighthSignup.objects \
                                 .filter(scheduled_activity__block=block) \
                                 .values_list("scheduled_activity__activity_id") \
                                 .annotate(user_count=Count("scheduled_activity"))

        for activity, user_count in activities:
            activity_list[activity]["roster"]["count"] = user_count

        sponsors_dict = EighthSponsor.objects \
                                     .all() \
                                     .values_list("id",
                                                  "user_id",
                                                  "first_name",
                                                  "last_name")

        all_sponsors = dict((sponsor[0],
                             {"user_id": sponsor[1],
                              "name": sponsor[3]}) for sponsor in sponsors_dict)

        activity_ids = scheduled_activities.values_list("activity__id")
        sponsorships = EighthActivity.sponsors \
                                     .through \
                                     .objects \
                                     .filter(eighthactivity_id__in=activity_ids) \
                                     .select_related("sponsors") \
                                     .values("eighthactivity", "eighthsponsor")

        scheduled_activity_ids = scheduled_activities.values_list("id", flat=True)
        overidden_sponsorships = \
            EighthScheduledActivity.sponsors \
            .through \
            .objects \
            .filter(eighthscheduledactivity_id__in=scheduled_activity_ids) \
            .values("eighthscheduledactivity", "eighthsponsor")

        for sponsorship in sponsorships:
            activity_id = int(sponsorship["eighthactivity"])
            sponsor_id = sponsorship["eighthsponsor"]
            sponsor = all_sponsors[sponsor_id]

            if sponsor["user_id"]:
                user = User.get_user(id=sponsor["user_id"])
                if user is not None:
                    name = user.last_name
                else:
                    name = None
            else:
                name = None

            activity_list[activity_id]["sponsors"] \
                .append(sponsor["name"] or name)

        for sponsorship in overidden_sponsorships:
            scheduled_activity_id = sponsorship["eighthscheduledactivity"]
            activity_id = scheduled_activity_to_activity_map[scheduled_activity_id]
            sponsor_id = sponsorship["eighthsponsor"]
            sponsor = all_sponsors[sponsor_id]

            if sponsor["user_id"]:
                user = User.get_user(id=sponsor["user_id"])
                if user is not None:
                    name = user.last_name
                else:
                    name = None
            else:
                name = None

            activity_list[activity_id]["sponsors"] \
                .append(sponsor["name"] or name)

        roomings = EighthActivity.rooms \
                                 .through \
                                 .objects \
                                 .filter(eighthactivity_id__in=activity_ids) \
                                 .select_related("eighthroom", "eighthactivity")
        overidden_roomings = \
            EighthScheduledActivity.rooms \
                                   .through \
                                   .objects \
                                   .filter(eighthscheduledactivity_id__in=
                                           scheduled_activity_ids) \
                                   .select_related("eighthroom",
                                                   "eighthscheduledactivity")

        for rooming in roomings:
            activity_id = rooming.eighthactivity.id
            room_name = rooming.eighthroom.name
            activity_list[activity_id]["rooms"].append(room_name)
            activity_list[activity_id]["roster"]["capacity"] += \
                rooming.eighthroom.capacity

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
            activity_list[activity_id]["roster"]["capacity"] += \
                rooming.eighthroom.capacity

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
            "url": reverse("api_eighth_block_detail",
                           args=[signup.scheduled_activity.block.id],
                           request=self.context["request"])
        }

    def activity_info(self, signup):
        return signup.scheduled_activity.activity.id

    def scheduled_activity_info(self, signup):
        return signup.scheduled_activity.id

    class Meta:
        model = EighthSignup
        fields = ("id",
                  "block",
                  "activity",
                  "scheduled_activity",
                  "user")
