# import the User object
from django.contrib.auth.models import User
import pexpect
import uuid
import os


# os.system("/usr/bin/kdestroy")

class KerberosAuthenticationBackend:
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
        # Try to find a user matching your username
        # user = User.objects.get(username=username)

        user = User()

        if KerberosAuthenticationBackend.kerberos_authenticate(username, password):
            # Populate user object here
            return user
        else:
            # No? return None - triggers default login failed
            return None

    # Required for your backend to work properly - unchanged in most scenarios
    def get_user(self, username):
        try:
            # return User.objects.get(pk=username)
            return User()
        except User.DoesNotExist:
            return None
