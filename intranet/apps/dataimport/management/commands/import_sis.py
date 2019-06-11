# -*- coding: utf-8 -*-

import os
import sys
import json
import csv
import re
import time
from typing import Dict, List  # noqa

from django.core.management.base import BaseCommand

from intranet.apps.users.models import User


class Command(BaseCommand):
    help = "Import data from SIS."

    def add_arguments(self, parser):
        parser.add_argument('--run', action='store_true', dest='run', default=False, help='Actually run.')
        parser.add_argument('--confirm', action='store_true', dest='confirm', default=False, help='Skip confirmation message.')
        parser.add_argument('--csv', type=str, dest='csv_file', default='import.csv', help='Import CSV file')
        parser.add_argument('--fake-teachers', action='store_true', dest='fake_teachers', default=False, help='Fake teacher names and room numbers')
        parser.add_argument('--load-users', action='store_true', dest='load_users', default=False, help='Load users into database')
        parser.add_argument('--teacher-mappings', type=str, dest='teacher_file', default='teacher.csv', help='Import Teacher mappings')

    def ask(self, q):
        if input("{} [Yy]: ".format(q)).lower() != "y":
            self.stdout.write("Abort.")
            sys.exit()

    def chk(self, q, test):
        if test:
            self.stdout.write("OK: %s" % q)
        else:
            self.stdout.write("ERROR: %s" % q)
            self.stdout.write("Abort.")
            sys.exit()

    csv_file = None  # type: str
    do_run = None  # type: bool
    uidmap = {}  # type: Dict[str,str]
    last_uid_number = 33971
    schedules = {}  # type: Dict[str,str]
    ldifs = {"newstudents": [], "oldstudents": [], "schedules": [], "newteachers": []}  # type: Dict[str,List[str]]
    teacher_mappings = {}  # type: Dict[str,str]
    new_teachers = []  # type: List[Dict[str,str]]

    def handle(self, *args, **options):
        self.csv_file = options["csv_file"]
        self.do_run = options["run"]
        self.skip_confirm = options["confirm"]
        self.fake_teachers = options["fake_teachers"]
        self.load_users = options["load_users"]
        self.teacher_file = options["teacher_file"]

        if self.load_users:
            for i in range(self.last_uid_number, self.last_uid_number + 500):
                try:
                    u = User.objects.get(id=i)
                except User.DoesNotExist:
                    self.stdout.write("UID %d None" % i)
                else:
                    self.stdout.write("UID %d %s" % (i, u))
            return

        if self.do_run:
            if self.skip_confirm:
                self.stdout.write("Skipping confirmation.")
            else:
                self.ask("===== WARNING! =====\n\n"
                         "This script will DESTROY data! Ensure that you have a properly backed-up copy of your database before proceeding.\n\n"
                         "===== WARNING! =====\n\n"
                         "Continue?")
        else:
            self.stdout.write("In pretend mode.")

        self.stdout.write("CSV file: %s" % self.csv_file)

        if self.fake_teachers:
            if os.path.isfile("users_faked.json"):
                self.stdout.write("Loading faked teachers JSON")
                users = json.loads(open("users_faked.json", "r").read())
                self.stdout.write("JSON loaded")
            else:
                users = self.load_gen_users()
                self.stdout.write("Faking teachers...")
                for i in range(len(users)):
                    for classid in users[i]["classes"]:
                        classobj = users[i]["classes"][classid]
                        classobj["Room"] = "Dome"
                        classobj["TeacherStaffName"] = "Glazer, E."
                        classobj["Teacher"] = "Glazer, Evan"
                        users[i]["classes"][classid] = classobj

                open("users_faked.json", "w").write(json.dumps(users))
        else:
            users = self.load_gen_users()

        if os.path.isfile("users_uids.json"):
            self.stdout.write("Loading user existence/UIDnumbers info...")
            self.uidmap = json.loads(open("users_uids.json", "r").read())
            for i in range(len(users)):
                user = users[i]
                tjuser = user["user"]["TJUsername"].lower()
                user["uidNumber"] = self.uidmap[tjuser]["uidNumber"]
                user["ldapExists"] = self.uidmap[tjuser]["ldapExists"]
            self.stdout.write("Loaded")
        else:
            self.stdout.write("Check for user existence/generate iodineUidNumbers")
            for i in range(len(users)):
                user = users[i]
                tjuser = user["user"]["TJUsername"].lower()
                try:
                    ionuser = User.objects.get(username__iexact=tjuser)
                except User.DoesNotExist:
                    uid_number = self.last_uid_number + 1
                    self.last_uid_number += 1
                    user["uidNumber"] = uid_number
                    user["ldapExists"] = False
                else:
                    user["uidNumber"] = ionuser.id
                    user["ldapExists"] = True

                self.uidmap[tjuser] = {"uidNumber": user["uidNumber"], "ldapExists": user["ldapExists"]}
            self.stdout.write("Done")
            open("users_uids.json", "w").write(json.dumps(self.uidmap))

        self.stdout.write("Either add or modify accounts in LDAP")
        for i in range(len(users)):
            user = users[i]
            if user["ldapExists"]:
                self.stdout.write("%s MODIFY %s" % (user["user"]["TJUsername"], user["uidNumber"]))
                self.update_ldap_user(user)
            else:
                self.stdout.write("%s CREATE %s" % (user["user"]["TJUsername"], user["uidNumber"]))
                self.add_ldap_user(user)

        if os.path.isfile("schedules.json"):
            self.stdout.write("Loading schedules...")
            self.schedules = json.loads(open("schedules.json", "r").read())
            self.stdout.write("Loaded schedules")
        else:
            self.stdout.write("Handle schedules")
            self.schedules = {}
            for i in range(len(users)):
                classes = users[i]["classes"]
                for sid in classes:
                    if sid not in self.schedules:
                        self.schedules[sid] = classes[sid]

            with open("schedules.json", "w") as f:
                f.write(json.dumps(self.schedules))

        for sid in self.schedules:
            self.stdout.write("ADD SCHEDULE %s" % sid)
            self.add_ldap_class(self.schedules[sid])

        self.stdout.write("Adding new teachers")
        for teacher in self.new_teachers:
            self.stdout.write("Add teacher {}".format(teacher))
            self.ldifs["newteachers"].append(self.gen_add_teacher_ldif(teacher))

        open("newstudents.ldif", "w").write("\n\n".join(self.ldifs["newstudents"]))
        open("oldstudents.ldif", "w").write("\n\n".join(self.ldifs["oldstudents"]))
        open("schedules.ldif", "w").write("\n\n".join(self.ldifs["schedules"]))
        open("newteachers.ldif", "w").write("\n\n".join(self.ldifs["newteachers"]))

        return

    def load_gen_users(self):
        if os.path.isfile("users.json"):
            self.stdout.write("Loading JSON")
            users = json.loads(open("users.json", "r").read())
            self.stdout.write("JSON loaded")
        else:
            self.stdout.write("Generating JSON file")
            users = self.generate_sorted_dump()
            open("users.json", "w").write(json.dumps(users))
            self.stdout.write("JSON loaded")
        return users

    def generate_sorted_dump(self):
        users_dict = {}
        users_dict_base = "TJUsername"
        class_dict_base = "SectionID"

        with open(self.csv_file, 'r') as csv_open:
            csv_reader = csv.reader(csv_open)
            next(csv_reader)  # skip first line
            class_rows = [
                "Period", "EndPeriod", "Teacher", "TeacherStaffName", "Room", "SectionID", "CourseID", "CourseTitle", "CourseShortTitle",
                "CourseIDTitle", "CourseTitleId", "TermName", "TermCode", "TeacherAide", "TermOverride", "SectionEnterDate", "SectionLeaveDate",
                "MeetDays"
            ]
            rows = [
                "StudentID", "Gender", "Grade", "FirstName", "LastName", "MiddleName", "StudentName", "TJUsername", "Nickname", "Birthdate",
                "Gridcode", "Address", "City", "State", "Zipcode", "CityStateZip", "EthnicCode", "Language", "EnterDate", "LeaveDate", "Track",
                "Phone", "ScheduleHouse", "HomeroomTeacher", "HomeroomStaffName", "HomeroomName", "CounselorLast", "Counselor", "Locker",
                "LockerComb", "ADA", "Organization", "Period", "EndPeriod", "Teacher", "TeacherStaffName", "Room", "SectionID", "CourseID",
                "CourseTitle", "CourseShortTitle", "CourseIDTitle", "CourseTitleId", "TermName", "TermCode", "TeacherAide", "TermOverride",
                "SectionEnterDate", "SectionLeaveDate", "House", "AuditClass", "MeetDays", "FeeAmount", "FeeCategory", "FeeCode", "FeeDescription",
                "ParentName1", "Phone1", "Type1", "Extension1", "ParentName2", "Phone2", "Type2", "Extension2", "ParentName3", "Phone3", "Type3",
                "Extension3", "ParentName4", "Phone4", "Type4", "Extension4"
            ]
            for row in csv_reader:
                row_dict = {rows[i]: row[i] for i in range(len(row))}
                class_dict = {i: row_dict[i] for i in class_rows}
                for f in class_rows:
                    del row_dict[f]
                row_dict["TJUsername"] = row_dict["TJUsername"].lower()
                if row_dict[users_dict_base] not in users_dict:
                    users_dict[row_dict[users_dict_base]] = {"user": row_dict, "classes": {}}
                users_dict[row_dict[users_dict_base]]["classes"][class_dict[class_dict_base]] = class_dict

            users_list = []
            for usr in users_dict:
                users_list.append(users_dict[usr])

        users = sorted(users_list, key=lambda x: (x["user"]["LastName"], x["user"]["FirstName"], x["user"]["MiddleName"], x["user"]["StudentID"]))
        return users

    def gen_add_teacher_ldif(self, data):
        """
        dn: iodineUid=emglazer,ou=people,dc=tjhsst,dc=edu
        objectClass: tjhsstTeacher
        iodineUid: emglazer
        iodineUidNumber: 59
        header: TRUE
        style: default
        mailentries: -1
        cn: Evan Glazer
        sn: Glazer
        givenName: Evan
        chrome: TRUE
        mail: Evan.Glazer@fcps.edu
        startpage: news
        """

        ldif = """
dn: iodineUid={username},ou=people,dc=tjhsst,dc=edu
changetype: add
objectClass: tjhsstTeacher
iodineUid: {username}
iodineUidNumber: {uid}
uid: {uid}
header: TRUE
style: default
mailentries: -1
cn: {fullname}
sn: {lastname}
givenName: {firstname}
startpage: news
structuralObjectClass: tjhsstTeacher""".format(**data)
        return ldif

    def gen_add_ldif(self, data):

        ldif = """
dn: iodineUid={iodineUid},ou=people,dc=tjhsst,dc=edu
changetype: add
objectClass: tjhsstStudent
iodineUid: {iodineUid}
iodineUidNumber: {iodineUidNumber}
uid: {iodineUidNumber}
header: TRUE
locker: 0
startpage: news
perm-showmap: FALSE
eighthoffice-comments:: IA==
chrome: TRUE
eighthAgreement: FALSE
tjhsstStudentId: {tjhsstStudentId}
cn: {cn}
sn: {sn}
postalCode: {postalCode}
counselor: {counselor}
st: {st}
l: {l}
homePhone: {homePhone}
birthday: {birthday}
street: {street}
givenName: {givenName}
graduationYear: {graduationYear}
displayName: {displayName}
gender: {gender}
title: {title}
middlename: {middlename}
preferredPhoto: AUTO
style: i3-light
mailentries: -1
is-admin: FALSE
perm-showaddress: FALSE
perm-showtelephone: FALSE
perm-showbirthday: FALSE
perm-showpictures: FALSE
perm-showlocker: FALSE
perm-showeighth: FALSE
perm-showschedule: FALSE
perm-showtelephone-self: FALSE
perm-showbirthday-self: FALSE
perm-showmap-self: FALSE
perm-showpictures-self: FALSE
perm-showlocker-self: FALSE
perm-showaddress-self: FALSE
perm-showschedule-self: FALSE
perm-showeighth-self: FALSE
{classes}""".format(**data)
        if not data["middlename"]:
            ldif = ldif.replace("\nmiddlename: ", "")

        ldif = ldif.replace("\nhomePhone: ###-###-####", "")
        ldif = ldif.replace("\nhomePhone: \n", "\n")

        return ldif

    def gen_update_ldif(self, data):

        ldif = """
dn: iodineUid={iodineUid},ou=people,dc=tjhsst,dc=edu
changetype: {changetype}
replace: locker
locker: 0
-
replace: eighthAgreement
eighthAgreement: FALSE
-
replace: tjhsstStudentId
tjhsstStudentId: {tjhsstStudentId}
-
replace: cn
cn: {cn}
-
replace: sn
sn: {sn}
-
replace: postalCode
postalCode: {postalCode}
-
replace: counselor
counselor: {counselor}
-
replace: st
st: {st}
-
replace: l
l: {l}
-
replace: homePhone
homePhone: {homePhone}
-
replace: birthday
birthday: {birthday}
-
replace: street
street: {street}
-
replace: givenName
givenName: {givenName}
-
replace: graduationYear
graduationYear: {graduationYear}
-
replace: displayName
displayName: {displayName}
-
replace: gender
gender: {gender}
-
replace: title
title: {title}
-
replace: middlename
middlename: {middlename}
-
replace: enrolledclass
{classes}""".format(**data)
        if not data["middlename"]:
            ldif = ldif.replace("\n-\nreplace: middlename\nmiddlename: ", "")

        ldif = ldif.replace("\n-\nreplace: homePhone\nhomePhone: ###-###-####", "")
        ldif = ldif.replace("\n-\nreplace: homePhone\nhomePhone: \n", "\n")

        return ldif

    def format_counselor(self, name):
        return {
            'Burke, Sean': 37,
            'Martinez, Susan L.': 1035,
            'Scott, Alexa': 105,
            'Ketchem, Christina Z.': 468,
            'Hamblin, Kerry': 115,
            'See Counseling Office': 999,  # TBA TBA
            'Smith, Andrea G.': 9,
            'McAleer, Kacey': 165,
            'Freedman, Naomi L.': 110
        }[name]

    def format_birthday(self, bday):
        # bday = M/D/Y
        month, day, year = bday.split("/")
        if int(month) < 10:
            month = "0" + month

        if int(day) < 10:
            day = "0" + day
        # YYYYMMDD
        return "{}{}{}".format(year, month, day)

    def format_title(self, gender):
        return {"M": "Mr.", "F": "Ms."}[gender]

    def format_display_name(self, data):
        if data["user"]["MiddleName"]:
            return "{} {} {}".format(data["user"]["FirstName"], data["user"]["MiddleName"], data["user"]["LastName"])

        return "{} {}".format(data["user"]["FirstName"], data["user"]["LastName"])

    def format_classes(self, data):
        cl = ""
        for cid in data["classes"]:
            cl += "enrolledclass: tjhsstSectionId={},ou=schedule,dc=tjhsst,dc=edu\n".format(data["classes"][cid]["SectionID"])

        return cl

    def gen_student_fields(self, data, changetype):
        return {
            "changetype": changetype,
            "iodineUid": data["user"]["TJUsername"],
            "iodineUidNumber": data["uidNumber"],
            "tjhsstStudentId": data["user"]["StudentID"],
            "cn": "{} {}".format(data["user"]["FirstName"], data["user"]["LastName"]),
            "sn": data["user"]["LastName"],
            "postalCode": data["user"]["Zipcode"],
            "counselor": self.format_counselor(data["user"]["Counselor"]),
            "st": data["user"]["State"],
            "l": data["user"]["City"],
            "homePhone": data["user"]["Phone"],
            "birthday": self.format_birthday(data["user"]["Birthdate"]),
            "street": data["user"]["Address"],
            "givenName": data["user"]["FirstName"],
            "graduationYear": data["user"]["TJUsername"][0:4],
            "displayName": self.format_display_name(data),
            "gender": data["user"]["Gender"],
            "title": self.format_title(data["user"]["Gender"]),
            "middlename": data["user"]["MiddleName"],
            "classes": self.format_classes(data)
        }

    def add_ldap_user(self, user_dict):
        fields = self.gen_student_fields(user_dict, "add")
        ldif = self.gen_add_ldif(fields)
        self.ldifs["newstudents"].append(ldif)
        self.stdout.write(str(user_dict))
        self.stdout.write(str(fields))
        self.stdout.write(ldif)
        self.stdout.write("\n")

    def update_ldap_user(self, user_dict):
        fields = self.gen_student_fields(user_dict, "modify")
        ldif = self.gen_update_ldif(fields)
        self.ldifs["oldstudents"].append(ldif)
        self.stdout.write(str(user_dict))
        self.stdout.write(str(fields))
        self.stdout.write(ldif)
        self.stdout.write("\n")

    def gen_class_ldif(self, data):
        """
dn: tjhsstSectionId=000900-05,ou=schedule,dc=tjhsst,dc=edu
objectClass: tjhsstClass
tjhsstClassId: 000900
tjhsstSectionId: 000900-05
courseLength: 4
quarterNumber: 1
quarterNumber: 2
quarterNumber: 3
quarterNumber: 4
roomNumber: DSS
graduationYear: 2016
cn: See Counselor
sponsorDn: iodineUid=mscox,ou=people,dc=tjhsst,dc=edu
classPeriod: 5
structuralObjectClass: tjhsstClass
        """

        return """
dn: tjhsstSectionId={sectionId},ou=schedule,dc=tjhsst,dc=edu
changetype: add
objectClass: tjhsstClass
tjhsstClassId: {classId}
tjhsstSectionId: {sectionId}
courseLength: {courseLength}
{quarters}
roomNumber: {roomNumber}
graduationYear: 2017
cn: {cn}
{periods}
sponsorDn: iodineUid={sponsor},ou=people,dc=tjhsst,dc=edu""".format(**data)

    def format_courselength(self, data):
        if data["TermCode"] == "YR":
            return 4

        if data["TermCode"] == "S1" or data["TermCode"] == "S2":
            return 2

    def format_quarters(self, data):
        if data["TermCode"] == "YR":
            return "\n".join(["quarterNumber: 1", "quarterNumber: 2", "quarterNumber: 3", "quarterNumber: 4"])

        if data["TermCode"] == "S1":
            return "\n".join(["quarterNumber: 1", "quarterNumber: 2"])

        if data["TermCode"] == "S2":
            return "\n".join(["quarterNumber: 3", "quarterNumber: 4"])

    def format_periods(self, data):
        if data["Period"] == data["EndPeriod"]:
            return "classPeriod: {}".format(data["Period"])

        return "\n".join(["classPeriod: {}".format(data["Period"]), "classPeriod: {}".format(data["EndPeriod"])])

    def format_sponsor(self, data):
        # TODO: Search existing LDAP/handle new teachers
        if data["Teacher"] in self.teacher_mappings:
            return self.teacher_mappings[data["Teacher"]]
        try:
            res = re.findall(r"^([\w\- ]+), ([\w\- ]+)(?: ([\w\-])\.)?$", data["Teacher"])[0]
            last_name, first_name, middle_initial = res
        except IndexError:
            if data["Teacher"]:
                self.stdout.write("INVALID TEACHER '{}' returning kosatka".format(data["Teacher"]))
                time.sleep(5)
            return 'bpkosatka'

        try:

            with open(self.teacher_file, 'r') as csv_file:
                reader = csv.reader(csv_file)
                next(reader)
                for line in reader:
                    if line[0] == last_name and line[1] == first_name and (not line[2] or not middle_initial or line[2].startswith(middle_initial)):
                        username = line[4].split('@')[0].lower()
            if not username:
                raise Exception("no match")

        except Exception as e:
            self.stdout.write(str(e))
            username = input("Please enter fcps username for {}: ".format(data["Teacher"]))

        self.teacher_mappings[data["Teacher"]] = username

        try:
            User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            uid_number = self.last_uid_number + 1
            self.last_uid_number += 1
            self.new_teachers.append({
                'uid': uid_number,
                'username': username,
                'firstname': first_name,
                'lastname': last_name,
                'fullname': '{} {}'.format(first_name, last_name)
            })
        return username

    def gen_class_fields(self, data):
        return {
            "sectionId": data["SectionID"],
            "classId": data["CourseID"],
            "courseLength": self.format_courselength(data),
            "quarters": self.format_quarters(data),
            "periods": self.format_periods(data),
            "roomNumber": data["Room"] or 'DSS',
            "cn": data["CourseTitle"],
            "sponsor": self.format_sponsor(data)
        }

    def add_ldap_class(self, data):
        fields = self.gen_class_fields(data)
        ldif = self.gen_class_ldif(fields)
        self.ldifs["schedules"].append(ldif)
        self.stdout.write(str(data))
        self.stdout.write(str(fields))
        self.stdout.write(ldif)
        self.stdout.write("\n\n")
