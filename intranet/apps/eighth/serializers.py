from django.db.models import Count
from rest_framework import serializers
from rest_framework.reverse import reverse
from .models import EighthBlock, EighthActivity, EighthSignup, EighthSponsor, EighthScheduledActivity
from intranet.apps.users.models import User
# from intranet.apps.users.serializers import UserSerializer


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
    class Meta:
        model = EighthBlock
        # Omit activities so people can't kill the database
        fields = ("id",
                  "url",
                  "date",
                  "block_letter",
                  "locked")


class EighthBlockDetailSerializer(serializers.Serializer):
    id = serializers.Field()
    url = serializers.HyperlinkedIdentityField(view_name="eighthblock-detail")

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
                "activity_id": scheduled_activity.activity.id,
                "scheduled_activity_id": scheduled_activity.id,
                "url": reverse("eighthactivity-detail", args=[scheduled_activity.activity.id], request=self.context["request"]),
                "name": scheduled_activity.activity.name,
                "description": scheduled_activity.activity.description,
                "roster": {
                    "count": 0,
                    "capacity": 0,
                    "url": "http://foobar.com"
                },
                "rooms": [],
                "sponsors": []
            }
            scheduled_activity_to_activity_map[scheduled_activity.id] = \
                scheduled_activity.activity.id

            activity_list[scheduled_activity.activity.id] = \
                activity_info

        activities = EighthSignup.objects \
                                 .filter(activity__block=block) \
                                 .values_list("activity__activity_id") \
                                 .annotate(user_count=Count("activity"))

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

        return activity_list

    class Meta:
        fields = ("id",
                  "activities",
                  "date",
                  "block_letter")


class EighthSignupSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="eighthsignup-detail")
    block = serializers.SerializerMethodField("block_id")
    activity = serializers.SerializerMethodField("activity_id")

    def block_id(self, signup):
        return reverse("eighthblock-detail", args=[signup.activity.block.id], request=self.context["request"])

    def activity_id(self, signup):
        return signup.activity.activity.id

    class Meta:
        model = EighthSignup
        fields = ("id",
                  "url",
                  "block",
                  "activity",
                  "user")
