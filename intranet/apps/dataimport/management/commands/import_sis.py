# -*- coding: utf-8 -*-

import sys
import json
import csv
import datetime
from django.conf import settings
from django.core.management.base import BaseCommand
from intranet.apps.users.models import User


class Command(BaseCommand):
    help = "Import data from SIS."

    def add_arguments(self, parser):
        parser.add_argument('--run', action='store_true', dest='run', default=False, help='Actually run.')
        parser.add_argument('--csv', type=str, dest='csv_file', default='import.csv', help='Import CSV file')
        parser.add_argument('--fake-teachers', action='store_true', dest='fake_teachers', default=False, help='Fake teacher names and room numbers')

    def ask(self, q):
        if input("{} [Yy]: ".format(q)).lower() != "y":
            print("Abort.")
            sys.exit()

    def chk(self, q, test):
        if test:
            print("OK:", q)
        else:
            print("ERROR:", q)
            print("Abort.")
            sys.exit()


    def handle(self, *args, **options):
        csv_file = options["csv_file"]
        do_run = options["run"]

        if do_run:
            self.ask("===== WARNING! =====\n\n"
                     "This script will DESTROY data! Ensure that you have a properly backed-up copy of your database before proceeding.\n\n"
                     "===== WARNING! =====\n\n"
                     "Continue?")
        else:
            print("In pretend mode.")


        print("CSV file", csv_file)

        users_dict = {}
        users_dict_base = "TJUsername"
        class_dict_base = "SectionID"

        with open(csv_file, 'r') as csv_open:
            csv_reader = csv.reader(csv_open)
            next(csv_reader)  # skip first line
            class_rows = [
                "Period", "EndPeriod", "Teacher", "TeacherStaffName", "Room", "SectionID", "CourseID", "CourseTitle", "CourseShortTitle",
                "CourseIDTitle", "CourseTitleId", "TermName", "TermCode", "TeacherAide", "TermOverride", "SectionEnterDate", "SectionLeaveDate",
                "MeetDays"
            ]
            rows = ["StudentID", "Gender", "Grade", "FirstName", "LastName", "MiddleName", "StudentName", "TJUsername", "Nickname", "Birthdate",
                    "Gridcode", "Address", "City", "State", "Zipcode", "CityStateZip", "EthnicCode", "Language", "EnterDate", "LeaveDate", "Track",
                    "Phone", "ScheduleHouse", "HomeroomTeacher", "HomeroomStaffName", "HomeroomName", "CounselorLast", "Counselor", "Locker",
                    "LockerComb", "ADA", "Organization", "Period", "EndPeriod", "Teacher", "TeacherStaffName", "Room", "SectionID", "CourseID",
                    "CourseTitle", "CourseShortTitle", "CourseIDTitle", "CourseTitleId", "TermName", "TermCode", "TeacherAide", "TermOverride",
                    "SectionEnterDate", "SectionLeaveDate", "House", "AuditClass", "MeetDays", "FeeAmount", "FeeCategory", "FeeCode",
                    "FeeDescription", "ParentName1", "Phone1", "Type1", "Extension1", "ParentName2", "Phone2", "Type2", "Extension2", "ParentName3",
                    "Phone3", "Type3", "Extension3", "ParentName4", "Phone4", "Type4", "Extension4"]
            for row in csv_reader:
                row_dict = {rows[i]: row[i] for i in range(len(row))}
                class_dict = {i: row_dict[i] for i in class_rows}
                if row_dict[users_dict_base] not in users_dict:
                    users_dict[row_dict[users_dict_base]] = {"user": row_dict, "classes": {}}
                users_dict[row_dict[users_dict_base]]["classes"][class_dict[class_dict_base]] = class_dict

            print("Check for users")
            open("udict.json", "w").write(json.dumps(users_dict))
            return
            for student_id in users_dict:
                user_dict = users_dict[student_id]
                sid = student_id.lower()
                if not sid:
                    print("Blank studentid")
                    print(user_dict)
                    break

                try:
                    user = User.objects.get(username=sid)
                except User.DoesNotExist:
                    #print("User does not exist with username '{}'".format(sid))
                    #print(user_dict)
                    self.add_ldap_user(user_dict)
                    continue
                #print(user, user_dict["classes"].keys())

            print(self.uidmap)
            return
            for student_id in users_dict:
                user_dict = users_dict[student_id]
                if not do_run:
                    continue

                for class_id in user_dict["classes"]:
                    class_obj = user_dict["classes"][class_id]
                    """try:
                        ldap_course = LDAPCourse.objects.get(course_id=class_obj["CourseID"], section_id=class_obj["SectionID"])

                    except LDAPCourse.DoesNotExist:
                        ldap_course = LDAPCourse.objects.create(
                            course_id=class_obj["CourseID"], section_id=class_obj["SectionID"], course_title=class_obj["CourseTitle"],
                            course_short_title=class_obj["CourseShortTitle"], teacher_name=class_obj["Teacher"], room_name=class_obj["Room"],
                            term_code=class_obj["TermCode"], period=class_obj["Period"], end_period=class_obj["EndPeriod"])
                    ldap_course.users.add(user)
                    ldap_course.save()"""
                    print("{} \t\tadded to\t\t {}".format(user, ldap_course))

    last_uid_number = 33503
    def get_ldif(self, data):
        """
        dn: iodineUid=2016jwoglom,ou=people,dc=tjhsst,dc=edu
        objectClass: tjhsstStudent
        iodineUid: 2016jwoglom
        iodineUidNumber: 31863
        uid: 31863
        header: TRUE
        startpage: news
        perm-showmap: FALSE
        eighthoffice-comments:: IA==
        chrome: TRUE
        eighthAgreement: TRUE
        perm-showaddress: TRUE
        perm-showtelephone: TRUE
        perm-showbirthday: TRUE
        perm-showpictures: TRUE
        perm-showlocker: TRUE
        perm-showeighth: TRUE
        perm-showschedule: TRUE
        style: i3-light
        mailentries: -1
        perm-showtelephone-self: TRUE
        perm-showbirthday-self: TRUE
        perm-showmap-self: FALSE
        perm-showpictures-self: TRUE
        perm-showlocker-self: TRUE
        is-admin: TRUE
        perm-showaddress-self: FALSE
        perm-showschedule-self: FALSE
        perm-showeighth-self: FALSE
        """
        ldif =("dn: iodineUid={TJUsername},ou=people,dc=tjhsst,dc=edu\n"
               "objectClass: tjhsstStudent\n"
               "iodineUid: {TJUsername}\n"
               "iodineUidNumber: {uidNumber}\n"
               "uid: {uidNumber}\n"
               "header: TRUE\n"
               "startpage: news\n"
               "perm-showmap: FALSE\n"
               "eighthoffice-comments:: IA==\n"
               "chrome: TRUE\n"
               "eighthAgreement: FALSE\n"
               "perm-showaddress: FALSE\n"
               "perm-showtelephone: FALSE\n"
               "perm-showbirthday: FALSE\n"
               "perm-showpictures: FALSE\n"
               "perm-showlocker: FALSE\n"
               "perm-showschedule: FALSE\n"
               "perm-showtelephone-self: FALSE\n"
               "perm-showbirthday-self: FALSE\n"
               "perm-showmap-self: FALSE\n"
               "perm-showlocker-self: FALSE\n"
               "perm-showaddress-self: FALSE\n"
               "perm-showschedule-self: FALSE\n"
               "perm-showeighth-self: FALSE\n"
               "style: i3-light\n"
               "mailentries: -1\n"
               "is-admin: FALSE\n").format(**data)
        return ldif

    uidmap = {}
    def add_ldap_user(self, user_dict):
        data = user_dict["user"]
        uidNumber = self.last_uid_number + 1
        self.last_uid_number += 1
        data["uidNumber"] = uidNumber
        #print(data)
        ldif = self.get_ldif(data)
        #print(ldif,"\n\n")
        self.uidmap[uidNumber] = data["TJUsername"]

