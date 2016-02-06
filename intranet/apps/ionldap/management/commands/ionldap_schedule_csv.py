# -*- coding: utf-8 -*-

import csv
from django.core.management.base import BaseCommand

from intranet.apps.groups.models import Group
from intranet.apps.users.models import User
from intranet.apps.ionldap.models import LDAPCourse


class Command(BaseCommand):
    help = "Import student and class data from a Kosatka-formatted CSV file."

    def add_arguments(self, parser):
        parser.add_argument('--csv',
                            type=str,
                            dest='csv_file',
                            default='import.csv',
                            help='Import CSV file')
        parser.add_argument('--add',
                            action='store_true',
                            dest='add',
                            default=False,
                            help='Add to database.')

    def handle(self, *args, **options):

        csv_file = options["csv_file"]
        add_db = options["add"]

        print("CSV file", csv_file)

        users_dict = {}
        users_dict_base = "TJUsername"
        class_dict_base = "SectionID"

        with open(csv_file, 'r') as csv_open:
            csv_reader = csv.reader(csv_open)
            next(csv_reader)  # skip first line
            CLASS_ROWS = [
                "Period",
                "EndPeriod",
                "Teacher",
                "TeacherStaffName",
                "Room",
                "SectionID",
                "CourseID",
                "CourseTitle",
                "CourseShortTitle",
                "CourseIDTitle",
                "CourseTitleId",
                "TermName",
                "TermCode",
                "TeacherAide",
                "TermOverride",
                "SectionEnterDate",
                "SectionLeaveDate",
                "MeetDays"
            ]
            ROWS = ["StudentID",
                    "Gender",
                    "Grade",
                    "FirstName",
                    "LastName",
                    "MiddleName",
                    "StudentName",
                    "TJUsername",
                    "Nickname",
                    "Birthdate",
                    "Gridcode",
                    "Address",
                    "City",
                    "State",
                    "Zipcode",
                    "CityStateZip",
                    "EthnicCode",
                    "Language",
                    "EnterDate",
                    "LeaveDate",
                    "Track",
                    "Phone",
                    "ScheduleHouse",
                    "HomeroomTeacher",
                    "HomeroomStaffName",
                    "HomeroomName",
                    "CounselorLast",
                    "Counselor",
                    "Locker",
                    "LockerComb",
                    "ADA",
                    "Organization",
                    "Period",
                    "EndPeriod",
                    "Teacher",
                    "TeacherStaffName",
                    "Room",
                    "SectionID",
                    "CourseID",
                    "CourseTitle",
                    "CourseShortTitle",
                    "CourseIDTitle",
                    "CourseTitleId",
                    "TermName",
                    "TermCode",
                    "TeacherAide",
                    "TermOverride",
                    "SectionEnterDate",
                    "SectionLeaveDate",
                    "House",
                    "AuditClass",
                    "MeetDays",
                    "FeeAmount",
                    "FeeCategory",
                    "FeeCode",
                    "FeeDescription",
                    "ParentName1",
                    "Phone1",
                    "Type1",
                    "Extension1",
                    "ParentName2",
                    "Phone2",
                    "Type2",
                    "Extension2",
                    "ParentName3",
                    "Phone3",
                    "Type3",
                    "Extension3",
                    "ParentName4",
                    "Phone4",
                    "Type4",
                    "Extension4"
                    ]
            for row in csv_reader:
                row_dict = {ROWS[i]: row[i] for i in range(len(row))}
                class_dict = {i: row_dict[i] for i in CLASS_ROWS}
                if row_dict[users_dict_base] not in users_dict:
                    users_dict[row_dict[users_dict_base]] = {
                        "user": row_dict,
                        "classes": {}
                    }
                users_dict[row_dict[users_dict_base]]["classes"][class_dict[class_dict_base]] = class_dict

            for student_id in users_dict:
                user_dict = users_dict[student_id]
                user = None
                try:
                    user = User.objects.get(username=student_id)
                except User.DoesNotExist:
                    print("User {} does not exist".format(student_id))
                if not add_db:
                    break

                for class_id in user_dict["classes"]:
                    class_obj = user_dict["classes"][class_id]
                    try:
                        ldap_course = LDAPCourse.objects.get(course_id=class_obj["CourseID"],
                                                             section_id=class_obj["SectionID"])

                    except LDAPCourse.DoesNotExist:
                        ldap_course = LDAPCourse.objects.create(course_id=class_obj["CourseID"],
                                                                section_id=class_obj["SectionID"],
                                                                course_title=class_obj["CourseTitle"],
                                                                course_short_title=class_obj["CourseShortTitle"],
                                                                teacher_name=class_obj["Teacher"],
                                                                room_name=class_obj["Room"],
                                                                term_code=class_obj["TermCode"],
                                                                period=class_obj["Period"],
                                                                end_period=class_obj["EndPeriod"]
                                                                )
                    ldap_course.users.add(user)
                    ldap_course.save()
                    print("{} \t\tadded to\t\t {}".format(user, ldap_course))
