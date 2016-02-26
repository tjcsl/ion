# -*- coding: utf-8 -*-
from unittest import mock

from typing import Any  # noqa

# FIXME: make more general, load from fixtures
all_users = '(|(objectclass=simpleUser)(objectclass=tjhsstStudent)(objectclass=tjhsstTeacher)(objectclass=tjhsstUser))'
uid_dn = 'iodineUid=awilliam,ou=people,dc=tjhsst,dc=edu'
counselor_dn = 'iodineUid=rms,ou=people,dc=tjhsst,dc=edu'
class_dn = 'tjhsstClassId=123456-78,ou=schedule,dc=tjhsst,dc=edu'
values = {
    ('ou=people,dc=tjhsst,dc=edu', '(iodineUidNumber=1337)', ('dn',)): [{'dn': uid_dn}],
    ('ou=people,dc=tjhsst,dc=edu', '(iodineUidNumber=420)', ('dn',)): [{'dn': counselor_dn}],
    ('ou=people,dc=tjhsst,dc=edu', '(graduationYear=2016)', ('dn',)): [{'dn': uid_dn}],
    ('ou=people,dc=tjhsst,dc=edu', '(graduationYear=2017)', ('dn',)): [],
    ('ou=people,dc=tjhsst,dc=edu', '(graduationYear=2018)', ('dn',)): [],
    ('ou=people,dc=tjhsst,dc=edu', '(graduationYear=2019)', ('dn',)): [],
}  # type: Dict[Any,Any]


def get_attr(dn, filt, attr, value):
    return {(dn, filt, (attr,)): [{'attributes': {attr: [value]}}]}


attrs = [('iodineUidNumber', 1337), ('iodineUid', 'awilliam'), ('objectClass', 'tjhsstStudent'), ('givenName', 'Angela'), ('gender', 'F'),
         ('title', 'HRH'), ('displayName', 'Angela'), ('cn', 'Angela'), ('middlename', 'dank'), ('sn', 'Williams'), ('nickname', 'Active Directory'),
         ('mail', 'bob@bob.com'), ('graduationYear', 2016), ('birthday', '1337420'), ('homePhone', '1234567890'), ('mobile', '1234567890'),
         ('telephoneNumber', '1234567890'), ('webpage', 'dankmemes.net'), ('counselor', 420), ('enrolledclass', class_dn)]  # type: List[Any]
for x, y in attrs:
    values.update(get_attr(uid_dn, all_users, x, y))
cattrs = [('iodineUidNumber', 420), ('iodineUid', 'rms'), ('objectClass', 'tjhsstTeacher'), ('cn', 'Richard'), ('sn', 'Stallman')]  # type: List[Any]
for x, y in cattrs:
    values.update(get_attr(counselor_dn, all_users, x, y))
class_attrs = [('classPeriod', 8), ('quarterNumber', 5), ('cn', 'Memes 101'), ('sponsorDn', counselor_dn)]  # type: List[Any]
for x, y in class_attrs:
    values.update(get_attr(class_dn, '(objectclass=tjhsstClass)', x, y))
perms = ('perm-showaddress', 'perm-showtelephone', 'perm-showbirthday', 'perm-showschedule', 'perm-showeighth', 'perm-showpictures',
         'perm-showaddress-self', 'perm-showtelephone-self', 'perm-showbirthday-self', 'perm-showschedule-self', 'perm-showeighth-self',
         'perm-showpictures-self')
values[(uid_dn, all_users, perms)] = [{'attributes': {x: [True] for x in perms}}]
street = ('street', 'l', 'st', 'postalCode')
values[(uid_dn, all_users, street)] = [{'attributes': {x: ['memes'] for x in street}}]


class MockLDAPConnection(mock.MagicMock):

    def search(self, dn, filter, attributes):
        attributes = tuple(attributes)
        if (dn, filter, attributes) in values:
            self.response = values[(dn, filter, attributes)]
            return
        raise Exception("UNIMPLEMENTED: %s  %s  %s" % (dn, filter, attributes))
