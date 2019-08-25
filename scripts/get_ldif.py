from django.forms.models import model_to_dict
from intranet.apps.users.models import User
import sys


def run(*args):
    if len(args) != 2:
        sys.exit(1)
    u = User.objects.get(username=args[0])
    uidNum = args[1]
    if u.user_type in ["teacher", "service", "counselor"]:
        u.graduation_year = 1984
        u.user_type = "staff"
    else:
        u.user_type = "students"

    ldiftemplate = """dn: uid={username},ou={graduation_year},ou={user_type},ou=people,dc=csl,dc=tjhsst,dc=edu
cn: {first_name} {last_name}
description: {graduation_year}
displayName: {last_name}, {first_name}
givenName: {first_name}
uid: {username}
sn: {last_name}
objectClass: inetOrgPerson
objectClass: top
objectClass: organizationalPerson
objectClass: person
objectClass: posixAccount
uidNumber: {uidNum}
gecos: {first_name} {last_name}
gidNumber: {graduation_year}
homeDirectory: /afs/csl.tjhsst.edu/{user_type}/{graduation_year}/{username}
loginShell: /bin/bash"""
    out = ldiftemplate.format(uidNum=uidNum, **model_to_dict(u))
    if u.user_type == "staff":
        out = out.replace("staff/1984", "staff")
        out = out.replace("ou=1984,", "")

    print(out)
