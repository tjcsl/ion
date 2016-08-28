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
    ldifs = []
    def handle(self, *args, **options):
        self.csv_file = options["csv_file"]
        self.do_run = options["run"]
        self.fake_teachers = options["fake_teachers"]

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
                users = load_gen_users()
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


        open("update.ldif", "w").write("\n\n".join(self.ldifs))
        
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
                if row_dict[users_dict_base] not in users_dict:
                    users_dict[row_dict[users_dict_base]] = {"user": row_dict, "classes": {}}
                users_dict[row_dict[users_dict_base]]["classes"][class_dict[class_dict_base]] = class_dict

            users_list = []
            for usr in users_dict:
                users_list.append(users_dict[usr])

        users = sorted(users_list, key=lambda x: (x["user"]["LastName"], x["user"]["FirstName"], x["user"]["MiddleName"], x["user"]["StudentID"]))
        return users            


    
    def get_ldif(self, data):
        
        ldif = """
dn: iodineUid={iodineUid},ou=people,dc=tjhsst,dc=edu
changetype: {changetype}
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
        """.format(**data)
        if not data["middlename"]:
            ldif = ldif.replace("\nmiddlename: ", "")

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

    def gen_fields(self, data, changetype):
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
            "middlename": data["user"]["MiddleName"]
        }

    def add_ldap_user(self, user_dict):
        fields = self.gen_fields(user_dict, "add")
        ldif = self.get_ldif(fields)
        self.ldifs.append(ldif)
        print(user_dict)
        print(fields)
        print(ldif)
        print("\n")
        

    def update_ldap_user(self, user_dict):
        fields = self.gen_fields(user_dict, "modify")
        ldif = self.get_ldif(fields)
        self.ldifs.append(ldif)
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

        base = """
dn: tjhsstSectionId={sectionId},ou=schedule,dc=tjhsst,dc=edu
objectClass: tjhsstClass
structuralObjectClass: tjhsstClass
tjhsstClassId: {classId}
tjhsstSectionId: {sectionId}
courseLength: {courseLength}
roomNumber: {roomNumber}
graduationYear: 2017
cn: {cn}
sponsorDn: iodineUid={sponsor},ou=people,dc=tjhsst,dc=edu
        """
        if data["courseLength"] == 4:
            base += "quarterNumber: 1\n"
            base += "quarterNumber: 2\n"
            base += "quarterNumber: 3\n"
            base += "quarterNumber: 4\n"


    def gen_class_fields(self, data):
        pass

