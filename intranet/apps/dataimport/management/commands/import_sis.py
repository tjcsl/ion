# -*- coding: utf-8 -*-

import os
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
        parser.add_argument('--load-users', action='store_true', dest='load_users', default=False, help='Load users into database')

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

    csv_file = None
    do_run = None
    uidmap = {}
    last_uid_number = 33503
    schedules = {}
    ldifs = {
        "newstudents": [],
        "oldstudents": [],
        "schedules": []
    }
    def handle(self, *args, **options):
        self.csv_file = options["csv_file"]
        self.do_run = options["run"]
        self.fake_teachers = options["fake_teachers"]
        self.load_users = options["load_users"]

        if self.load_users:
            for i in range(self.last_uid_number, self.last_uid_number + 500):
                try:
                    u = User.get_user(id=i)
                except User.DoesNotExist:
                    print("UID", i, "None")
                else:
                    print("UID", i, u)
            return

        if self.do_run:
            self.ask("===== WARNING! =====\n\n"
                     "This script will DESTROY data! Ensure that you have a properly backed-up copy of your database before proceeding.\n\n"
                     "===== WARNING! =====\n\n"
                     "Continue?")
        else:
            print("In pretend mode.")


        print("CSV file", self.csv_file)
        


        if self.fake_teachers:
            if os.path.isfile("users_faked.json"):
                print("Loading faked teachers JSON")
                users = json.loads(open("users_faked.json", "r").read())
                print("JSON loaded")
            else:
                users = self.load_gen_users()
                print("Faking teachers...")
                for i in range(len(users)):
                    for classid in users[i]["classes"]:
                        classobj = users[i]["classes"][classid]
                        classobj["Room"] = "Dome"
                        classobj["TeacherStaffName"] = "Glazer, E."
                        classobj["Teacher"] = "Glazer, Evan"
                        users[i]["classes"][classid] = classobj

                open("users_faked.json", "w").write(json.dumps(users))


        if os.path.isfile("users_uids.json"):
            print("Loading user existence/UIDnumbers info...")
            self.uidmap = json.loads(open("users_uids.json", "r").read())
            for i in range(len(users)):
                user = users[i]
                tjuser = user["user"]["TJUsername"].lower()
                user["uidNumber"] = self.uidmap[tjuser]["uidNumber"]
                user["ldapExists"] = self.uidmap[tjuser]["ldapExists"]
            print("Loaded")
        else:
            print("Check for user existence/generate iodineUidNumbers")
            for i in range(len(users)):
                user = users[i]
                tjuser = user["user"]["TJUsername"].lower()
                try:
                    ionuser = User.objects.get(username__iexact=tjuser)
                except User.DoesNotExist:
                    uidNumber = self.last_uid_number + 1
                    self.last_uid_number += 1
                    user["uidNumber"] = uidNumber
                    user["ldapExists"] = False
                else:
                    user["uidNumber"] = ionuser.id
                    user["ldapExists"] = True

                self.uidmap[tjuser] = {"uidNumber": user["uidNumber"], "ldapExists": user["ldapExists"]}
            print("Done")
            open("users_uids.json", "w").write(json.dumps(self.uidmap))

        print("Either add or modify accounts in LDAP")
        for i in range(len(users)):
            user = users[i]
            if user["ldapExists"]:
                print(user["user"]["TJUsername"], "MODIFY", user["uidNumber"])
                self.update_ldap_user(user)
            else:
                print(user["user"]["TJUsername"], "CREATE", user["uidNumber"])
                self.add_ldap_user(user)

        if os.path.isfile("schedules.json"):
            print("Loading schedules...")
            self.schedules = json.loads(open("schedules.json", "r").read())
            print("Loaded schedules")
        else:
            print("Handle schedules")
            self.schedules = {}
            for i in range(len(users)):
                classes = users[i]["classes"]
                for sid in classes:
                    if sid not in schedules:
                        self.schedules[sid] = classes[sid]

            open("schedules.json", "w").write(json.dumps(self.schedules))


        for sid in self.schedules:
            print("ADD SCHEDULE", sid)
            self.add_ldap_class(self.schedules[sid])

        open("newstudents.ldif", "w").write("\n\n".join(self.ldifs["newstudents"]))
        open("oldstudents.ldif", "w").write("\n\n".join(self.ldifs["oldstudents"]))
        open("schedules.ldif", "w").write("\n\n".join(self.ldifs["schedules"]))
        
        return

    def load_gen_users(self):
        if os.path.isfile("users.json"):
            print("Loading JSON")
            users = json.loads(open("users.json", "r").read())
            print("JSON loaded")
        else:
            print("Generating JSON file")
            users = self.generate_sorted_dump()
            open("users.json", "w").write(json.dumps(users))
            print("JSON loaded")
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
replace: perm-showaddress
perm-showaddress: FALSE
-
replace: perm-showtelephone
perm-showtelephone: FALSE
-
replace: perm-showbirthday
perm-showbirthday: FALSE
-
replace: perm-showpictures
perm-showpictures: FALSE
-
replace: perm-showlocker
perm-showlocker: FALSE
-
replace: perm-showeighth
perm-showeighth: FALSE
-
replace: perm-showschedule
perm-showschedule: FALSE
-
replace: perm-showtelephone-self
perm-showtelephone-self: FALSE
-
replace: perm-showbirthday-self
perm-showbirthday-self: FALSE
-
replace: perm-showmap-self
perm-showmap-self: FALSE
-
replace: perm-showpictures-self
perm-showpictures-self: FALSE
-
replace: perm-showlocker-self
perm-showlocker-self: FALSE
-
replace: perm-showaddress-self
perm-showaddress-self: FALSE
-
replace: perm-showschedule-self
perm-showschedule-self: FALSE
-
replace: perm-showeighth-self
perm-showeighth-self: FALSE
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
            'Martinez, Susan L.': 152, # Kosatka
            'Scott, Alexa': 105,
            'Ketchem, Christina Z.': 468,
            'Hamblin, Kerry': 115,
            'See Counseling Office': 999, # TBA TBA
            'Smith, Andrea G.': 9,
            'McAleer, Kacey': 165
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
        return {
            "M": "Mr.",
            "F": "Ms."
        }[gender]

    def format_displayName(self, data):
        if len(data["user"]["MiddleName"] or "") > 0:
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
            "displayName": self.format_displayName(data),
            "gender": data["user"]["Gender"],
            "title": self.format_title(data["user"]["Gender"]),
            "middlename": data["user"]["MiddleName"],
            "classes": self.format_classes(data)
        }

    def add_ldap_user(self, user_dict):
        fields = self.gen_student_fields(user_dict, "add")
        ldif = self.gen_add_ldif(fields)
        self.ldifs["newstudents"].append(ldif)
        print(user_dict)
        print(fields)
        print(ldif)
        print("\n")
        

    def update_ldap_user(self, user_dict):
        fields = self.gen_student_fields(user_dict, "modify")
        ldif = self.gen_update_ldif(fields)
        self.ldifs["oldstudents"].append(ldif)
        print(user_dict)
        print(fields)
        print(ldif)
        print("\n")


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
            return ("quarterNumber: 1\n"
                    "quarterNumber: 2\n"
                    "quarterNumber: 3\n"
                    "quarterNumber: 4")

        if data["TermCode"] == "S1":
            return ("quarterNumber: 1\n"
                    "quarterNumber: 2")

        if data["TermCode"] == "S2":
            return ("quarterNumber: 3\n"
                    "quarterNumber: 4")

    def format_periods(self, data):
        if data["Period"] == data["EndPeriod"]:
            return "classPeriod: {}".format(data["Period"])

        return ("classPeriod: {}\n"
                "classPeriod: {}".format(data["Period"], data["EndPeriod"]))

    def format_sponsor(self, data):
        # TODO: Search existing LDAP/handle new teachers
        return {
            "Glazer, Evan": 59
        }[data["Teacher"]]

    def gen_class_fields(self, data):
        return {
            "sectionId": data["SectionID"],
            "classId": data["CourseID"],
            "courseLength": self.format_courselength(data),
            "quarters": self.format_quarters(data),
            "periods": self.format_periods(data),
            "roomNumber": data["Room"],
            "cn": data["CourseTitle"],
            "sponsor": self.format_sponsor(data)
        }

    def add_ldap_class(self, data):
        fields = self.gen_class_fields(data)
        ldif = self.gen_class_ldif(fields)
        self.ldifs["schedules"].append(ldif)
        print(data)
        print(fields)
        print(ldif)
        print("\n\n")

