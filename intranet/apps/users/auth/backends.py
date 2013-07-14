# import the User object
import pexpect
import uuid
import os
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist


# os.system("/usr/bin/kdestroy")

class KerberosAuthenticationBackend(object):
    create_unknown_user = False

    @classmethod
    def kerberos_authenticate(self, username, password):
        ad_realm = "LOCAL.TJHSST.EDU"
        csl_realm = "CSL.TJHSST.EDU"
        cache = "/tmp/authtest-" + str(uuid.uuid4())

        print("Cache file is " + cache)

        os.environ['KRB5CCNAME'] = cache

        kinit = pexpect.spawn("/usr/bin/kinit {}@{}".format(username, csl_realm))
        kinit.expect("{}@{}'s Password:".format(username, csl_realm))
        kinit.sendline(password)
        kinit.expect(pexpect.EOF)
        kinit.close()
        exitstatus = kinit.exitstatus

        if(exitstatus):
            kinit = pexpect.spawn("/usr/bin/kinit {}@{}".format(username, ad_realm))
            kinit.expect("{}@{}'s Password:".format(username, ad_realm))
            kinit.sendline(password)
            kinit.expect(pexpect.EOF)
            kinit.close()
            exitstatus = exitstatus or kinit.exitstatus

        if(kinit.exitstatus == 0):
            return True
        else:
            return False

    def authenticate(self, username=None, password=None):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User.objects.create(username=username)
            user.set_unusable_password()

        if KerberosAuthenticationBackend.kerberos_authenticate(username, password):
            return user
        else:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
