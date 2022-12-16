#!/usr/bin/env python3

import os
import django
import argparse
import names
import random
from datetime import datetime
from dateutil.relativedelta import relativedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "intranet.settings")
django.setup()

from intranet.apps.groups.models import Group  # noqa: E402
from intranet.apps.users.models import User  # noqa: E402

GRADES = ["freshman", "sophomore", "junior", "senior"]


def grade_to_year(year: str) -> str:
    delta = 0
    if year == "freshman":
        delta = 3
    if year == "sophomore":
        delta = 2
    if year == "junior":
        delta = 1
    if year == "senior":
        delta = 0

    # if it is from august -> december add 1
    if datetime.now().month > 7:
        delta += 1
    
    return (datetime.now() + relativedelta(years=delta)).strftime("%Y")

def create_teachers(args: argparse.Namespace) -> None:
    for first_name, last_name, username in args.names:
        username = validate(username)
        user = User.objects.get_or_create(first_name=first_name, last_name=last_name, username=username, user_type="teacher")[0]
        user.save()
        if args.verbose:
            print(f"Created teacher \"{first_name} {last_name}\" ({username})")


def create_students(args: argparse.Namespace) -> None:
    for first_name, last_name, username in args.names:
        username = validate(username)
        user = User.objects.get_or_create(first_name=first_name, last_name=last_name, username=username)[0]
        if not args.noyear:
            user.graduation_year = username[:4]
        user.save()
        if args.verbose:
            print(f"Created student \"{first_name} {last_name}\" ({username})")


def create_admins(args: argparse.Namespace) -> None:
    group = Group.objects.get_or_create(name="admin_all")[0]
    for first_name, last_name, username in args.names:
        username = validate(username)
        user = User.objects.get_or_create(first_name=first_name, last_name=last_name, username=username)[0]
        if not args.noyear:
            user.graduation_year = username[:4]
        user.groups.add(group)
        user.is_superuser = True
        user.save()
        if args.verbose:
            print(f"Created admin \"{first_name} {last_name}\" ({username})")


def validate(username: str) -> str:
    if User.objects.filter(username=username):
        username += "1"
        while User.objects.filter(username=username):
            end = int(username[-1])
            username = username[:-1] + str(end + 1)
    return username


def generate_names(args: argparse.Namespace) -> list[tuple[str]]:
    for i, name in enumerate(args.names):
        username = ""
        if not args.noyear and args.type != "teacher":
            username = grade_to_year(args.year if args.year else random.choice(GRADES))
        if name:
            if "_" in name:
                first_name, last_name = name.split("_")
                username += first_name[0].lower() + last_name[:7].lower()
            else:
                first_name = name
                last_name = name
                username += name
        else:
            first_name, last_name = names.get_full_name(gender=args.gender).split(" ")
            username += first_name[0].lower() + last_name[:7].lower()
        args.names[i] = (first_name, last_name, username)
    return args.names

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--names", nargs="+", default=[], help="Provide in format first_last, or as a username, ignores count if supplied, seperate with '_'")
    parser.add_argument("-c", "--count", type=int, default=10, help="Number of users to make, defaults to 10")
    parser.add_argument("-t", "--type", type=str, required=True, choices=["student", "teacher", "admin"], help="type of user to make")
    parser.add_argument("-ny", "--noyear", action="store_true", help="does not prepend username with year, ignores year flag")
    parser.add_argument("-y", "--year", type=str, required=False, choices=GRADES, help="Year of student, doesn't do anything for teachers, defaults to random")
    parser.add_argument("-g", "--gender", type=str, required=False, choices=["male", "female"], help="Gender of user's name, defaults to either")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enables verbose output")
    args = parser.parse_args()
    if not args.names:
        args.names = [None] * args.count
    args.names = generate_names(args)
    if args.type == "student":
        create_students(args)
    elif args.type == "teacher":
        create_teachers(args)
    elif args.type == "admin":
        create_admins(args)


if __name__ == "__main__":
    main()
    