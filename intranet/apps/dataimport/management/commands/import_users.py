import json

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q


class Command(BaseCommand):
    help = "Import User Objects"

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument("data_fname")

    def handle(self, *args, **kwargs):
        try:
            with open(kwargs["data_fname"]) as f_obj:
                data = json.load(f_obj)
        except OSError as ex:
            raise CommandError(str(ex)) from ex

        for counselor in data["counselors"]:
            gender = counselor["Gender"].strip()
            first_name = counselor["First Name"].strip()
            last_name = counselor["Last Name"].strip()
            username = counselor["User Name"].strip()

            get_user_model().objects.get_or_create(
                username=username, defaults={"last_name": last_name, "first_name": first_name, "user_type": "counselor", "gender": (gender == "M")},
            )

        for teacher in data["teachers"]:
            gender = teacher["Gender"].strip()
            first_name = teacher["First Name"].strip()
            last_name = teacher["Last Name"].strip()
            username = teacher["User Name"].strip()

            get_user_model().objects.get_or_create(
                username=username, defaults={"last_name": last_name, "first_name": first_name, "user_type": "teacher", "gender": (gender == "M")}
            )

        for student in data["students"]:
            sid = student["Student ID"]
            gender = student["Gender"].strip()
            first_name = student["First Name"].strip()
            last_name = student["Last Name"].strip()
            middle_name = student["Middle Name"].strip()
            username = student["User Name"].strip()
            nickname = student["Nick Name"].strip()
            counselor_names = student["Counselor"].strip().split(", ")
            graduation_year = int(username[:4])

            counselor = get_user_model().objects.get(last_name=counselor_names[0])
            if not get_user_model().objects.filter(Q(username=username) | Q(student_id=sid)).exists():
                get_user_model().objects.create(
                    student_id=sid,
                    last_name=last_name,
                    first_name=first_name,
                    username=username,
                    counselor=counselor,
                    gender=(gender == "M"),
                    graduation_year=graduation_year,
                    middle_name=middle_name,
                    nickname=nickname,
                    receive_news_emails=True,
                    receive_eighth_emails=True,
                )

        if "alumni" in data:
            for alum in data["alumni"]:
                gender = alum["Gender"].strip()
                first_name = alum["First Name"].strip()
                last_name = alum["Last Name"].strip()
                username = alum["User Name"].strip()

                get_user_model().objects.get_or_create(
                    username=username, defaults={"last_name": last_name, "first_name": first_name, "user_type": "teacher", "gender": (gender == "M")},
                )
