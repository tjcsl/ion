import csv
import sys

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from intranet.apps.eighth.models import EighthActivity, EighthBlock, EighthRoom, EighthScheduledActivity, EighthSignup, EighthSponsor


class Command(BaseCommand):
    help = (
        "Given a CSV of tjSTAR data, create the eighth periods in Ion. Required columns "
        "in the CSV include 'Capacity', 'Room (for Sysadmins)', 'Block {A,B,C}.{1,2} Lab', "
        "'Block {A,B,C}.{1,2} Project', and 'Block {A,B,C}.{1,2} Student IDs'"
    )
    shorthands = (
        ("Chemistry Analysis/Nanochemistry", "Chemistry"),
        ("Astronomy and Astrophysics", "Astronomy"),
        ("Engineering Design", "Engineering"),
        ("Biotechnology and Life Sciences", "Biotech"),
        ("Mobile and Web App Development", "Mobile / Web"),
        (", ", " + "),  # multiple labs same project
    )

    def add_arguments(self, parser):
        parser.add_argument("filename")

    def handle(self, *args, **options):
        with open(options["filename"], "r", encoding="utf-8") as csv_file:
            data = csv.DictReader(csv_file)

            for idx, row in enumerate(data):
                for block_letter in ("A", "B", "C"):
                    try:
                        capacity = int(row["Capacity"])
                        room_name = row["Room (for Sysadmins)"]
                        room = EighthRoom.objects.filter(name=room_name).first()

                        room_hosts = row["Room Hosts"].split(", ")
                        sponsors = []
                        for host in room_hosts:
                            host = host.strip()
                            if " " in host:
                                first_name, last_name = host.split(" ")

                                teacher = EighthSponsor.objects.filter(first_name=first_name, last_name=last_name)
                                if not teacher.exists():
                                    teacher = EighthSponsor.objects.filter(last_name=host)

                                sponsors.append(teacher.first())
                            else:
                                teacher = EighthSponsor.objects.filter(last_name=host).first()
                                sponsors.append(teacher)
                        sponsors = [s for s in sponsors if s is not None]

                        lab_1 = row[f"Block {block_letter}.1 Lab"]
                        lab_2 = row[f"Block {block_letter}.2 Lab"]

                        project_1 = row[f"Block {block_letter}.1 Project"]
                        project_2 = row[f"Block {block_letter}.2 Project"]

                        student_ids_1 = row[f"Block {block_letter}.1 Student IDs"].split(", ")
                        student_ids_2 = row[f"Block {block_letter}.2 Student IDs"].split(", ")
                        users_1 = get_user_model().objects.filter(student_id__in=student_ids_1)
                        users_2 = get_user_model().objects.filter(student_id__in=student_ids_2)

                        eighth_block = EighthBlock.objects.get_or_create(
                            date=settings.TJSTAR_DATE,
                            block_letter=f"TJ STAR-{block_letter}",
                        )[0]

                        activity_name = f"{lab_1} & {lab_2}" if lab_2 else lab_1
                        for name, shorthand in Command.shorthands:
                            activity_name = activity_name.replace(name, shorthand)

                        activity_description = f'"{project_1}" - {", ".join(u.display_name for u in users_1)}'
                        if project_2:
                            activity_description += f'\n\n"{project_2}" - {", ".join(u.display_name for u in users_2)}'

                        eighth_activity = EighthActivity.objects.get_or_create(
                            name=activity_name,
                            description=activity_description,
                        )[0]
                        eighth_activity.sponsors.set(sponsors)
                        eighth_activity.rooms.set((room,))

                        eighth_scheduled_activity = EighthScheduledActivity.objects.get_or_create(
                            activity=eighth_activity,
                            block=eighth_block,
                            capacity=capacity,
                        )[0]

                        users = users_1 | users_2
                        for user in users:
                            current_signup = EighthSignup.objects.filter(
                                user=user,
                                scheduled_activity__block=eighth_scheduled_activity.block,
                            )
                            if current_signup.exists():
                                current_signup.delete()

                            EighthSignup(user=user, scheduled_activity=eighth_scheduled_activity).save()

                    except Exception as e:
                        sys.stderr.write(f"Error processing row: {idx + 1}\n")
                        raise CommandError(str(e)) from e
