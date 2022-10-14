#!/usr/bin/env python3
import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "intranet.settings")
django.setup()

from intranet.apps.groups.models import Group  # noqa: E402
from intranet.apps.users.models import User  # noqa: E402

"""
    This script creates users based on command line arguments.
"""


def help():
    print()
    print("Command line utility for creating Intranet users.")
    print()
    print("SYNTAX: python create-users.py [USER TYPE] [USERNAMES]")
    print()
    print("USER TYPES:")
    print("-s  --student | Create normal (student) user.")
    print("-t  --teacher | Create teacher.")
    print("-a  --admin   | Create admin (superuser).")
    print()
    print("USERNAMES:")
    print("Space-separated list of usernames.")
    print()

    sys.exit(0)


def success_message(user_type):
    length = len(sys.argv) - 2

    if length > 1:  # plural
        user_type = user_type + "s"

    print("Successfully created " + str(length) + " " + user_type + ":")
    for name in sys.argv[2:]:
        if sys.argv.index(name) == len(sys.argv) - 1:
            print(name)
        else:
            print(name, end=", ")

    sys.exit(0)


def create_students():
    for name in sys.argv[2:]:
        user = User.objects.get_or_create(username=name)[0]
        user.save()
    success_message("student")


def create_teachers():
    for name in sys.argv[2:]:
        user = User.objects.get_or_create(username=name, user_type="teacher")[0]
        user.save()
    success_message("teacher")


def create_admins():
    for name in sys.argv[2:]:
        user = User.objects.get_or_create(username=name)[0]
        group = Group.objects.get_or_create(name="admin_all")[0]
        user.groups.add(group)
        user.is_superuser = True
        user.save()
    success_message("admin")


# Run
if len(sys.argv) == 1:
    help()

option = sys.argv[1]

if option in ("-s", "--student"):
    create_students()
elif option in ("-t", "--teacher"):
    create_teachers()
elif option in ("-a", "--admin"):
    create_admins()

help()
