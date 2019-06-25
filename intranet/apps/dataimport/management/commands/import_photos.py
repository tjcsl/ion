import os
import sys
import json
import csv
from django.core.management.base import BaseCommand
from intranet.apps.users.models import User


class Command(BaseCommand):
    help = "Import Lifetouch photos into LDAP. Uses the 'TJHSST-Intranet' photo data export format via the Lifetouch Portal."

    def add_arguments(self, parser):
        parser.add_argument('--pretend', action='store_true', dest='pretend', default=False, help="Don't save files to filesystem")
        parser.add_argument('--root', type=str, dest='root_dir', default='/root/photos/1617/DataImages/',
                            help='**absolute** path to outer DataImages folder for LDIF')
        parser.add_argument('--local-root', type=str, dest='local_root_dir', default='/mnt/c/Users/James/DataImages/',
                            help='path to DataImages folder on this host')
        parser.add_argument('--grade-offset', type=int, dest='grade_offset', default=0, help='Grade offset, for importing previous year photos')
        parser.add_argument('--skip-staff', action='store_true', dest='skip_staff', default=False, help='Skip staff')

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
        self.pretend = options["pretend"]
        self.root_dir = options["root_dir"]
        self.local_root_dir = options["local_root_dir"]
        self.grade_offset = options["grade_offset"]
        self.skip_staff = options["skip_staff"]

        print("GRADE OFFSET: ", self.grade_offset)
        print("\n".join(["{} => {}".format(i, self.calc_grade_offset(i)) for i in range(9, 13)]))
        teacher_photo_index = 0

        if os.path.isfile("user_sid_map.json"):
            users = json.loads(open("user_sid_map.json", "r").read())
        else:
            users = {}

            csv_path = "{}data.txt".format(self.local_root_dir)
            with open(csv_path, 'r') as csv_file:
                csv_reader = csv.reader(csv_file, delimiter='\t', quotechar='"')
                next(csv_reader)  # skip header
                # StudentID, FirstName, LastName, Grade
                for row in csv_reader:
                    print(row)
                    sid, fname, lname, grade = row
                    grade = self.fix_grade(grade)
                    if grade == 'IGNORE':
                        # ignore staff with pictures who aren't in LDAP
                        teacher_photo_index += 1
                        continue

                    current_grade = self.calc_grade_offset(grade)
                    if grade != 'STA' and (int(current_grade) > 12 or int(current_grade) < 9):
                        continue
                    # the CSV includes only "missing-Student ID", but we need the
                    # filename for each specific missing student id file.
                    if sid.startswith("missing-"):
                        sid = self.teacher_photo_name(teacher_photo_index)
                        teacher_photo_index += 1

                    entry = {"sid": sid, "fname": fname, "lname": lname, "grade": grade, "photo_name": sid}
                    if grade != "STA":
                        user_obj = self.get_from_sid(sid)
                        # entry["user_obj"] = user_obj
                    else:
                        user_obj = self.get_staff_name(fname, lname)

                    if not user_obj:
                        print("INVALID USER OBJECT", entry)
                        # if self.grade_offset != 0:
                        #    continue

                    entry["username"] = user_obj.username

                    users[entry["username"]] = entry

            if not self.pretend:
                open("user_sid_map.json", "w").write(json.dumps(users))

        print("Map loaded.")

        ldifs = []

        for uname in users:
            udata = users[uname]
            if self.skip_staff and udata["grade"] == "STA":
                continue

            photo_yr = self.photo_title_year(udata["grade"])

            if photo_yr:
                print("OK", uname, udata["grade"], photo_yr, users[uname])
                ldif = self.add_photo_ldif({"photo": photo_yr, "iodineUid": uname, "path": self.get_photo_path(udata["photo_name"])})

                ldifs.append(ldif)

                if udata["grade"] == "STA":
                    ldif = self.teacher_default_photo_ldif({"iodineUid": uname})
                    ldifs.append(ldif)
            else:
                print("SKIP", uname, udata["grade"], photo_yr)

        if not self.pretend:
            open("import_photos.ldif", "w").write("\n\n".join(ldifs))

    def get_from_sid(self, sid):
        # fix duplicate student ID map in LDAP
        sid = int(sid)
        if sid == 1582058:
            return User.objects.get(id=33494)
        if sid == 1163521:
            return User.objects.get(id=32391)
        return User.objects.user_with_student_id(sid)

    def get_staff_name(self, fname, lname):
        # ignore subnames in parens; wildcard for abbreviated names
        fname = fname.split('(')[0] + '*'
        lname = lname + '*'
        u = User.objects.user_with_name(fname, lname)
        if u:
            return u
        # hyphenated vs spaced subnames
        u = User.objects.user_with_name(fname, lname.replace(' ', '-'))
        if u:
            return u
        # non-spaced last name
        u = User.objects.user_with_name(fname, lname.replace(' ', ''))
        if u:
            return u
        # non-spaced first name
        u = User.objects.user_with_name(fname.replace(' ', ''), lname)
        if u:
            return u
        # middle name in first name
        u = User.objects.user_with_name(fname.split(' ')[0], lname)
        if u:
            return u
        # cathie => catherine
        u = User.objects.user_with_name(fname.lower().replace('ie', 'erine'), lname)
        if u:
            return u
        # mike => michael
        u = User.objects.user_with_name(fname.lower().replace('ke', 'chael'), lname)
        if u:
            return u
        # katrina => katy
        u = User.objects.user_with_name(fname.lower().replace('trina', 'ty'), lname)
        if u:
            return u
        # kathleen => kathy
        u = User.objects.user_with_name(fname.lower().replace('hleen', 'hy'), lname)
        if u:
            return u
        # If you got to here without a match... they probably aren't in LDAP.
        # change "STA" to "IGNORE" in the csv
        return None

    def calc_grade_offset(self, grade):
        if grade == "STA":
            return grade
        return int(grade) - (self.grade_offset or 0)

    def fix_grade(self, grade):
        grade = str(grade)
        if grade == 'NGA':
            return 'STA'
        if grade[-2:] == 'TH':
            return grade[:-2]
        if grade[-1:] == 'T':
            return grade[:-1]
        if grade[-1:] == 'H':
            return grade[:-1]

        return grade

    def photo_title_year(self, grade):
        gmap = {"9": "freshmanPhoto", "10": "sophomorePhoto", "11": "juniorPhoto", "12": "seniorPhoto", "STA": "freshmanPhoto"}
        if str(grade) in gmap:
            if grade != "STA" and int(grade) >= 9 and int(grade) <= 12:
                return gmap[str(grade)]
            elif grade == "STA":
                return gmap[str(grade)]

        return None

    def teacher_photo_name(self, index):
        if index == 0:
            return "missing-Student ID"
        return "missing-Student ID-{}".format(index)

    def get_photo_path(self, sid):
        return "{}images/{}.jpg".format(self.root_dir, sid)

    def delete_photo_ldif(self, data):
        ldif = """
dn: cn={photo},iodineUid={iodineUid},ou=people,dc=tjhsst,dc=edu
changetype: delete""".format(**data)

        return ldif

    def add_photo_ldif(self, data):
        ldif = """
dn: cn={photo},iodineUid={iodineUid},ou=people,dc=tjhsst,dc=edu
changetype: add
objectClass: iodinePhoto
cn: {photo}
jpegPhoto:< file://{path}""".format(**data)

        return ldif

    def teacher_default_photo_ldif(self, data):
        ldif = """
dn: iodineUid={iodineUid},ou=people,dc=tjhsst,dc=edu
changetype: modify
replace: preferredPhoto
preferredPhoto: freshmanPhoto
-
replace: perm-showpictures-self
perm-showpictures-self: TRUE""".format(**data)

        return ldif
