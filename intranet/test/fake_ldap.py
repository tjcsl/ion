from unittest import mock


# FIXME: make more general, load from fixtures
all_users = '(|(objectclass=simpleUser)(objectclass=tjhsstStudent)(objectclass=tjhsstTeacher)(objectclass=tjhsstUser))'
uid_dn = 'iodineUid=awilliam,ou=people,dc=tjhsst,dc=edu'
values = {
        (uid_dn,all_users,('iodineUidNumber',)): [{'attributes':{'iodineUidNumber':[1337]}}],
        (uid_dn,all_users,('iodineUid',)): [{'attributes':{'iodineUid':['awilliam']}}],
        (uid_dn,all_users,('objectClass',)): [{'attributes':{'objectClass':['tjhsstStudent']}}],
        (uid_dn,all_users,('givenName',)): [{'attributes':{'givenName':['Angela']}}],
        ('ou=people,dc=tjhsst,dc=edu','(iodineUidNumber=1337)',('dn',)): [{'dn':uid_dn}],
        }
        

class MockLDAPConnection(mock.MagicMock):
    def search(self, dn, filter, attributes):
        attributes = tuple(attributes)
        if (dn,filter,attributes) in values:
            self.response = values[(dn,filter,attributes)]
            return
        raise Exception("UNIMPLEMENTED: %s  %s  %s" % (dn,filter,attributes))
