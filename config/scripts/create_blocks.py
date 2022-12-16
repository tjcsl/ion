#!/usr/bin/env python3

import django
import os
import argparse
import string
from datetime import datetime, timedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "intranet.settings")
django.setup()

from intranet.apps.eighth.models import EighthBlock, EighthActivity, EighthScheduledActivity  # noqa: E402F

def generate_blocks(args: argparse.Namespace) -> None:
    activities = EighthActivity.objects.all()
    today = datetime.now()
    for i in range(args.count):
        date = (today + timedelta(days=i * args.interval)).strftime("%Y-%m-%d")
        for letter in args.letters:
            block = EighthBlock.objects.get_or_create(date=date, block_letter=letter)[0]
            block.save()
            for activity in activities:
                scheduled_activity = EighthScheduledActivity.objects.get_or_create(block=block, activity=activity)[0]
                scheduled_activity.capacity = activity.default_capacity
                scheduled_activity.save()

        if args.verbose:
            print(f"Created eighth period on {date} ({', '.join(args.letters)})")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--count", type=int, default=30, help="Number of eighth blocks to make, defaults to 30")
    parser.add_argument("-l", "--letters", type=str, nargs="+", required=True, choices=list(string.ascii_uppercase), help="Block letters")
    parser.add_argument("-i", "--interval", type=int, default=1, help="Interval in days between blocks, defaults to 1")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enables verbose output")
    args = parser.parse_args()
    generate_blocks(args)


if __name__ == "__main__":
    main()
