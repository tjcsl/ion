import json

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from intranet.apps.eighth.models import EighthActivity, EighthRoom, EighthSponsor


class Command(BaseCommand):
    help = "Import Eighth Period Activities For Testing"

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument("data_fname")

    def handle(self, *args, **kwargs):
        try:
            with open(kwargs["data_fname"]) as f_obj:
                data = json.load(f_obj)
        except OSError as ex:
            raise CommandError(str(ex)) from ex

        for activity in data["activities"]:
            name = activity["Name"].strip()
            description = activity["Description"].strip()
            sponsors = activity["Sponsor"]
            room_num = activity["Room Number"]
            capacity = activity["Capacity"]
            wed_a = activity["Wed A"]
            wed_b = activity["Wed B"]
            fri_a = activity["Fri A"]
            fri_b = activity["Fri B"]
            one_a_day = activity["One A-day"]
            both_blocks = activity["Both Blocks"]
            presign = activity["Presign"]
            special = activity["Special"]
            sticky = activity["Sticky"]
            administrative = activity["Administrative"]
            restricted = activity["Restricted"]

            room = EighthRoom.objects.get_or_create(name=room_num, capacity=capacity)[0]
            activity = EighthActivity.objects.get_or_create(
                name=name,
                description=description,
                default_capacity=capacity,
                presign=presign,
                one_a_day=one_a_day,
                sticky=sticky,
                special=special,
                administrative=administrative,
                restricted=restricted,
                both_blocks=both_blocks,
                wed_a=wed_a,
                wed_b=wed_b,
                fri_a=fri_a,
                fri_b=fri_b,
            )[0]
            activity.rooms.add(room)
            for sponsor in sponsors:
                sponsor_first_name, sponsor_last_name, sponsor_username, sponsor_gender = sponsor
                if not get_user_model().objects.filter(Q(username=sponsor_username)).exists():
                    sponsor_object = get_user_model().objects.create(
                        username=sponsor_username,
                        first_name=sponsor_first_name,
                        last_name=sponsor_last_name,
                        user_type="teacher",
                        gender=(sponsor_gender == "M"),
                    )
                else:
                    sponsor_object = get_user_model().objects.get(username=sponsor_username)

                sponsor = EighthSponsor.objects.get_or_create(
                    first_name=sponsor_object.first_name, last_name=sponsor_object.last_name, user=sponsor_object
                )[0]

                activity.sponsors.add(sponsor)
            activity.save()
