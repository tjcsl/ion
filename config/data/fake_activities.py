#!/usr/bin/env python3
import csv
import json
import random

# Constants
NUM_ACTIVITIES = 40
NUM_REGULAR = 20
OUTPUT_FILENAME = "outputs/eighth_import.json"
teacher_filename = "outputs/user_import.json"
ROOMLIST = set()
return_dict = {}

with open(teacher_filename) as f_obj:
    data = json.load(f_obj)
teachers = []
for teacher in data["teachers"]:
    gender = teacher["Gender"].strip()
    first_name = teacher["First Name"].strip()
    last_name = teacher["Last Name"].strip()
    username = teacher["User Name"].strip()
    teachers.append((first_name, last_name, username, gender))


def rand_activity(count):
    name = "activity" + str(count)
    description = name
    sponsor = assign_sponsor(count)
    rooms = count + 15
    if count == 5:
        rooms = "Cafeteria"
    elif count == 9:
        rooms = "Lecture Hall"
    capacity = random.randint(15, 100)
    wed_a, wed_b, fri_a, fri_b = get_date()
    one_a_day, both_blocks, presign, special, sticky, administrative, restricted = get_classification(count, wed_a, wed_b, fri_a, fri_b)
    to_return_list = []
    to_return_list.append(
        {
            "Name": name,
            "Description": description,
            "Sponsor": sponsor,
            "Room Number": rooms,
            "Capacity": capacity,
            "Wed A": wed_a,
            "Wed B": wed_b,
            "Fri A": fri_a,
            "Fri B": fri_b,
            "One A-day": one_a_day,
            "Both Blocks": both_blocks,
            "Presign": presign,
            "Special": special,
            "Sticky": sticky,
            "Administrative": administrative,
            "Restricted": restricted,
        }
    )
    return to_return_list


def assign_sponsor(count):
    num_sponsors = random.randint(1, 4)
    randlist = random.sample(range(0, len(teachers)), num_sponsors)
    return [teachers[x] for x in randlist]


def get_date():
    wed_a = random.randint(0, 1)
    wed_b = random.randint(0, 1)
    fri_a = random.randint(0, 1)
    fri_b = random.randint(0, 1)
    return wed_a == 1, wed_b == 1, fri_a == 1, fri_b == 1


def get_classification(count, wed_a, wed_b, fri_a, fri_b):
    one_a_day = False
    both_blocks = False
    if (wed_a and wed_b and not fri_a and not fri_b) or (fri_a and fri_b and not wed_a and not fri_b):
        one_a_day = random.randint(0, 1) == 1
        if not one_a_day:
            both_blocks = random.randint(0, 1) == 1
    presign = random.randint(1, 10) == 1
    sticky = False
    if not one_a_day:
        sticky = random.randint(1, 10) == 1
    special = False
    administrative = False
    restricted = False
    if count < 2:
        special = True
    elif not (one_a_day or both_blocks or presign or special):
        administrative = random.randint(1, 10) == 1
        restricted = random.randint(1, 10) == 1
    return one_a_day, both_blocks, presign, special, sticky, administrative, restricted


activity_list = []

for x in range(NUM_ACTIVITIES):
    per = rand_activity(x)
    for entry in per:
        activity_list.append(entry)
# print(activity_list)

fname = OUTPUT_FILENAME

return_dict["activities"] = activity_list
with open(fname, "w") as write_json:
    json.dump(return_dict, write_json)

print("Successfully wrote to {}".format(fname))
