#!/usr/bin/env python3

import argparse
import os
import random

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "intranet.settings")
django.setup()

from intranet.apps.eighth.models import EighthActivity, EighthRoom, EighthSponsor  # noqa: E402
from intranet.apps.groups.models import Group  # noqa: E402
from intranet.apps.users.models import User  # noqa: E402


def generate_activities(args: argparse.Namespace) -> None:
    ids = EighthActivity.available_ids()
    groups = [Group.objects.get_or_create(name=group)[0] for group in args.groups]
    teachers = User.objects.filter(user_type="teacher")
    for _, id in zip(range(args.count), ids):
        activity = EighthActivity.objects.get_or_create(name=f"Activity {id}")[0]
        activity.default_capacity = args.capacity if args.capacity else random.randint(10, 50)
        if args.restricted or args.groups:
            activity.restricted = True
        for restriction in args.restricted:
            if restriction == "freshman":
                activity.freshmen_allowed = True
            if restriction == "sophomore":
                activity.sophomores_allowed = True
            if restriction == "junior":
                activity.juniors_allowed = True
            if restriction == "senior":
                activity.seniors_allowed = True
        activity.save()

        sponser = EighthSponsor.objects.get_or_create(user=random.choice(teachers))[0]
        sponser.save()
        activity.sponsors.set((sponser,))

        room = EighthRoom.objects.get_or_create(name=f"Room {random.randint(1, 100)}")[0]
        room.save()
        activity.rooms.set((room,))

        activity.groups_allowed.set(groups)

        if args.verbose:
            if args.groups or args.restricted:
                print(f"Made activity {id}, restricted to ({', '.join(args.groups + args.restricted)})")
            else:
                print(f"Made activity {id}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--count", type=int, default=10, help="Number of activities to make, defaults to 10")
    parser.add_argument("-C", "--capacity", type=int, required=False, help="Capacity for each activity, defaults to random between 10 and 50")
    parser.add_argument(
        "-r",
        "--restricted",
        type=str,
        nargs="+",
        default=[],
        choices=["freshman", "sophomore", "junior", "senior"],
        help="Restricts activity access to one grade",
    )
    parser.add_argument("-g", "--groups", type=str, nargs="+", default=[], help="Groups to restrict access to")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enables verbose output")
    args = parser.parse_args()
    generate_activities(args)


if __name__ == "__main__":
    main()
