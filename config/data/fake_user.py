#!/usr/bin/env python3
import csv
import json
import random

# Constants
SENIOR_GRAD_YEAR = 2020
USERNAME_LAST_LENGTH = 7
NUM_STUDENTS = 1800
NUM_TEACHERS = 100
NUM_ALUMNI = 10
COUNSELORS = {
    1: ("Sean", "Burke", "M"),
    2: ("Christina", "Ketchem", "F"),
    3: ("Kerry", "Hamblin", "F"),
    4: ("Laurie", "Phelps", "F"),
    5: ("Kacey", "McAleer", "F"),
    6: ("Susan", "Martinez", "F"),
    7: ("Andrea", "Smith", "F"),
}

OUTPUT_JSON = "outputs/user_import.json"

filename = "social_security_list/yob{}.txt".format(random.randint(1880, 1943))
print("Reading %s for names" % filename)

with open(filename) as f:
    names = {tuple(line.split(",")[:2]): int(line.split(",")[2]) for line in f.read().split()}


def rand_name():
    number = random.randint(0, sum(names.values()) - 1)
    for (name, gender), occurrences in names.items():
        number -= occurrences
        if number <= 0:
            return name, gender

    return None


def get_tj_username(grade, f_name, l_name):
    grad_year = str(SENIOR_GRAD_YEAR + 12 - int(grade))
    if len(l_name) < USERNAME_LAST_LENGTH:
        last_string = l_name
    else:
        last_string = l_name[:7]

    return "{}{}{}".format(grad_year, f_name[:1], last_string).lower()


def get_teacher_username(f_name, l_name):
    if len(l_name) < USERNAME_LAST_LENGTH:
        last_string = l_name
    else:
        last_string = l_name[:7]

    return "{}{}".format(f_name[:1], last_string).lower()


current_id = 111111


def rand_pers(num):
    first, gender = rand_name()
    root_last, useless_gender = rand_name()

    if gender == "M":
        last = root_last + "son"
    elif gender == "F":
        last = root_last + "daughter"
    else:
        last = root_last

    grade = random.randint(9, 12)
    tj_username = get_tj_username(grade, first, last)
    student_name = "{} {}".format(first, last)
    middle = ""
    nickname = ""
    student_id = num

    counselor_choice = random.randint(1, 7)
    counselor = COUNSELORS[counselor_choice][1] + ", " + COUNSELORS[counselor_choice][0]
    counselor_last = COUNSELORS[counselor_choice][1]

    to_return_list = []
    to_return_list.append(
        {
            "Student ID": student_id,
            "Gender": gender,
            "Grade": grade,
            "First Name": first,
            "Last Name": last,
            "Middle Name": middle,
            "Full Name": student_name,
            "User Name": tj_username,
            "Nick Name": nickname,
            "Counselor": counselor,
        }
    )

    return to_return_list


def make_counselor():
    to_return_list = []
    grade = 13
    for counselor in COUNSELORS.values():
        first = counselor[0]
        last = counselor[1]
        counselor_name = "{} {}".format(first, last)
        counselor_username = get_teacher_username(first, last)
        to_return_list.append(
            {
                "Gender": counselor[2],
                "Grade": grade,
                "First Name": first,
                "Last Name": last,
                "Full Name": counselor_name,
                "User Name": counselor_username,
            }
        )
    return to_return_list


def rand_teacher():
    first, gender = rand_name()
    root_last, useless_gender = rand_name()

    if gender == "M":
        last = root_last + "son"
    elif gender == "F":
        last = root_last + "daughter"
    else:
        last = root_last

    grade = 13
    teacher_username = get_teacher_username(first, last)
    teacher_name = "{} {}".format(first, last)

    to_return_list = []
    to_return_list.append(
        {
            "Gender": gender,
            "Grade": grade,
            "First Name": first,
            "Last Name": last,
            "Full Name": teacher_name,
            "User Name": teacher_username,
        }
    )
    return to_return_list


def make_alum():
    first, gender = rand_name()
    root_last, useless_gender = rand_name()

    if gender == "M":
        last = root_last + "son"
    elif gender == "F":
        last = root_last + "daughter"
    else:
        last = root_last
    if len(last) < USERNAME_LAST_LENGTH:
        last_string = last
    else:
        last_string = last[:7]

    tj_username = "{}{}{}".format("2018", first[:1], last_string).lower()

    to_return_list = []
    to_return_list.append(
        {
            "Gender": gender,
            "Grade": 13,
            "First Name": first,
            "Last Name": last,
            "Full Name": "{} {}".format(first, last),
            "User Name": tj_username,
        }
    )
    return to_return_list


list_student = []
jsondict = {}

for x in range(NUM_STUDENTS):
    per = rand_pers(x + 111111)
    for entry in per:
        list_student.append(entry)
# print(list_student)

teacher_list = []

for x in range(NUM_TEACHERS):
    per = rand_teacher()
    for entry in per:
        teacher_list.append(entry)
# print(teacher_list)

counselor_list = []
per = make_counselor()
for entry in per:
    counselor_list.append(entry)
# print(counselor_list)

alum_list = []
for x in range(NUM_ALUMNI):
    per = make_alum()
    for entry in per:
        alum_list.append(entry)
# print(alum_list)

jsondict["students"] = list_student
jsondict["teachers"] = teacher_list
jsondict["counselors"] = counselor_list
jsondict["alum"] = alum_list

with open(OUTPUT_JSON, "w") as write_json:
    json.dump(jsondict, write_json)

print("Successfully wrote to {}".format(OUTPUT_JSON))
