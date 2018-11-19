#!/usr/bin/python
# -*- coding: utf-8 -*-

###############################################
#       WARNING WARNING WARNING WARNING       #
###############################################
#  This script was developed to run on IODINE #
#  as part of the conversion process between  #
#  Intranet2 and Intranet3. THIS SCRIPT DOES  #
#  NOT CREATE NEW ION FIXTURES. To do this,   #
#  run ./manage.py export_fixtures            #
###############################################

import datetime
import json
import os
import os.path
import re
import sys

import MySQLdb as mdb

import ldap3

import pexpect

# Run this on iodine.tjhsst.edu
start_date = "2015-09-01"
csl_realm = "CSL.TJHSST.EDU"
host = "iodine.tjhsst.edu"
ldap_realm = "CSL.TJHSST.EDU"
ldap_server = "ldap://iodine-ldap.tjhsst.edu"
base_dn = "ou=people,dc=tjhsst,dc=edu"

kgetcred = pexpect.spawn("/usr/bin/kgetcred ldap/{}@{}".format(host, ldap_realm))
kgetcred.expect(pexpect.EOF)
kgetcred.close()

if kgetcred.exitstatus:
    print("Authorization to LDAP failed. Try running kinit.")
    sys.exit(1)

print("Successfully authorized to LDAP service")

server = ldap3.Server(ldap_server)
connection = ldap3.Connection(server, authentication=ldap3.SASL, sasl_mechanism='GSSAPI')
connection.bind()
print("Successfully bound to LDAP with " + connection.extend.standard.who_am_i())


def user_attrs(uid, attr):
    sfilter = '(iodineUidNumber=' + str(uid) + ')'
    try:
        ri = connection.search(base_dn, sfilter)
        r = ri[0]['attributes']
    except IndexError:
        return ""
    return r[attr][0]


os.system("mkdir -p fixtures/{eighth,users,announcements}")

f_blocks = open("fixtures/eighth/blocks.json", "w")
f_activities = open("fixtures/eighth/activities.json", "w")
f_rooms = open("fixtures/eighth/rooms.json", "w")
f_s_activities = open("fixtures/eighth/scheduled_activities.json", "w")
f_sponsors = open("fixtures/eighth/sponsors.json", "w")
f_users = open("fixtures/users/users.json", "w")
f_signups = open("fixtures/eighth/signups.json", "w")
f_announcements = open("fixtures/announcements/announcements.json", "w")

con = mdb.connect("localhost", "iodine", input("Iodine MySQL password: "), "iodine")

cur = con.cursor()

eighth_objects = []
user_objects = []
user_pks = []
block_pks = []
blocks_map = {}
bad_sa = []
sponsor_pks = []
room_pks = []

# BLOCKS #
cur.execute("SELECT * FROM eighth_blocks WHERE date > '{}';".format(start_date))
rows = cur.fetchall()

for row in rows:
    obj = {
        "pk": row[0],
        "model": "eighth.EighthBlock",
        "fields": {
            "date": row[1].strftime("%Y-%m-%d"),
            "locked": row[3] == 1,
            "block_letter": row[2]
        }
    }
    eighth_objects.append(obj)
    block_pks.append(row[0])

json.dump(eighth_objects, f_blocks)
eighth_objects = []
print("Blocks complete")

# SPONSORS #
cur.execute("SELECT * FROM eighth_sponsors;")
rows = cur.fetchall()
seen_uids = set()

for row in rows:
    pk = row[0]
    uid = row[4]

    # Fix for old Lauducci ID number
    if uid == 1009:
        uid = 492

    if uid in [0, 2, 3, 138, 501, 910, 1009, 7004] or uid in seen_uids:
        uid = None
    else:
        seen_uids.add(uid)

    obj = {
        "pk": pk,
        "model": "eighth.EighthSponsor",
        "fields": {
            "user": uid,
            "first_name": row[1],
            "last_name": row[2],
            "online_attendance": row[3] == "onlin"
        }
    }
    eighth_objects.append(obj)
    sponsor_pks.append(pk)

    user_pk = uid
    if (user_pk is not None) and (user_pk not in user_pks):
        username = user_attrs(user_pk, "iodineUid")
        obj = {
            "pk": user_pk,
            "model": "users.User",
            "fields": {
                "username": username if username != "" else (row[1][:1] + row[2])[:15],
                "password": "!"
            }
        }
        if username != "":
            # print (row[1][:1] + row[2])[:15], user_pk
            user_objects.append(obj)
            user_pks.append(user_pk)

json.dump(eighth_objects, f_sponsors)
eighth_objects = []
print("Sponsors complete")
# print(sponsor_pks)

# ROOMS #
cur.execute("SELECT * FROM eighth_rooms;")
rows = cur.fetchall()

for row in rows:
    obj = {"pk": row[0], "model": "eighth.EighthRoom", "fields": {"name": re.sub(r" \(.*\)$", "", row[1]), "capacity": row[2]}}
    eighth_objects.append(obj)
    room_pks.append(row[0])

json.dump(eighth_objects, f_rooms)
eighth_objects = []
print("Rooms complete")

# ACTIVITIES #
cur.execute("SELECT * FROM eighth_activities;")
rows = cur.fetchall()

for row in rows:
    try:
        rooms = [int(i) for i in row[3].split(",") if int(i) in room_pks]
    except ValueError:
        rooms = []

    try:
        sponsors = [int(i) for i in row[2].split(",") if int(i) in sponsor_pks]
    except ValueError:
        sponsors = []

    obj = {
        "pk": row[0],
        "model": "eighth.EighthActivity",
        "fields": {
            "name": row[1],
            "sponsors": sponsors,
            "rooms": rooms,
            "description": row[4],
            "restricted": row[5],
            "presign": row[6],
            "one_a_day": row[7],
            "both_blocks": row[8],
            "sticky": row[9],
            "special": row[10]
        }
    }
    eighth_objects.append(obj)

json.dump(eighth_objects, f_activities)
eighth_objects = []
print("Activities complete")

# SCHEDULED ACTIVITIES #
cur.execute("SELECT * FROM eighth_block_map WHERE bid >= 2355;")
rows = cur.fetchall()

for pk, row in enumerate(rows):
    try:
        rooms = [int(i) for i in row[3].split(",") if int(i) in room_pks]
    except ValueError:
        rooms = []

    try:
        sponsors = [int(i) for i in row[2].split(",")]
    except ValueError:
        sponsors = []

    obj = {
        "pk": pk + 1,
        "model": "eighth.EighthScheduledActivity",
        "fields": {
            "block": row[0],
            "activity": row[1],
            "sponsors": sponsors,
            "rooms": rooms,
            "attendance_taken": row[4] == 1,
            "cancelled": row[5] == 1,
            "comments": row[7],
        }
    }

    if row[0] in block_pks:
        eighth_objects.append(obj)
    else:
        bad_sa.append(pk + 1)

    blocks_map[str(row[0]) + ":" + str(row[1])] = pk + 1

json.dump(eighth_objects, f_s_activities)
eighth_objects = []
print("Scheduled activities complete")

# SIGNUPS #
block_pk_str = ",".join(map(str, block_pks))
cur.execute("SELECT * FROM eighth_activity_map WHERE bid IN ({})".format(block_pk_str))
rows = cur.fetchall()

for pk, row in enumerate(rows):
    try:
        scheduled_activity = blocks_map[str(row[1]) + ":" + str(row[0])]
    except KeyError:
        pass
    else:
        obj = {
            "pk": pk + 1,
            "model": "eighth.EighthSignup",
            "fields": {
                "time": str(datetime.datetime.now()),
                "user": row[2],
                "scheduled_activity": scheduled_activity,
                "after_deadline": row[3] == 1
            }
        }
        if scheduled_activity not in bad_sa:
            eighth_objects.append(obj)

        user_pk = row[2]
        if user_pk not in user_pks:
            username = user_attrs(user_pk, "iodineUid")

            obj = {"pk": user_pk, "model": "users.User", "fields": {"username": username, "password": "!"}}
            user_objects.append(obj)
            user_pks.append(user_pk)

json.dump(eighth_objects, f_signups)
eighth_objects = []

json.dump(user_objects, f_users)
user_objects = []

print("Signups complete")
print("Users complete")

# ANNOUNCEMENTS #
cur.execute("SELECT * FROM news WHERE posted > '{}';".format(start_date))
rows = cur.fetchall()
news = []
for row in rows:
    date = row[4].strftime("%Y-%m-%d")
    author = user_attrs(row[3], "cn")

    obj = {
        "pk": row[0],
        "model": "announcements.Announcement",
        "fields": {
            "title": row[1],
            "content": row[2],
            "author": author,
            "added": date,
            "updated": date
        }
    }
    news.append(obj)

json.dump(news, f_announcements)
print("Announcements complete")

con.close()

f_blocks.close()
f_activities.close()
f_rooms.close()
f_s_activities.close()
f_users.close()
f_signups.close()
f_announcements.close()
