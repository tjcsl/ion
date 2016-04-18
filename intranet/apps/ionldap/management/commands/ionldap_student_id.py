# -*- coding: utf-8 -*-

import csv

from django.core.management.base import BaseCommand

from intranet.apps.users.models import User


class Command(BaseCommand):
    help = "Import student ID data from a SIS CSV export."
    """ To import: ./manage.py ionldap_student_id --csv /path/to/sis-dump.csv --add """

    def add_arguments(self, parser):
        parser.add_argument('--csv', type=str, dest='csv_file', default='import.csv', help='Import CSV file')
        parser.add_argument('--add', action='store_true', dest='add', default=False, help='Add to database.')

    def handle(self, *args, **options):

        csv_file = options["csv_file"]
        add_db = options["add"]

        print("CSV file", csv_file)

        users_dict = {}

        with open(csv_file, 'r') as csv_open:
            csv_reader = csv.reader(csv_open)
            next(csv_reader)  # skip first line
            # rows = ["StudentID", "Gender", "Grade", "FirstName", "LastName", "MiddleName", "StudentName", "TJUsername"]
            for row in csv_reader:
                # TJUsername = StudentID
                uname = row[7].lower()
                uid = int(row[0])
                if uname and uid and uname not in users_dict:
                    users_dict[uname] = uid
                    print(uname, uid)

        if not add_db:
            return

        for tjuser, fcpsid in users_dict.items():
            try:
                u = User.objects.get(username=tjuser)
                u._student_id = fcpsid
                u.save()
            except User.DoesNotExist:
                print("USER {} {} DOES NOT EXIST".format(tjuser, fcpsid))
