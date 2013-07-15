import os
import ldap
import ldap.sasl
import pexpect
import logging
from intranet.apps.users.models import User
from intranet.db.ldap import connection
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

logger = logging.getLogger(__name__)


@login_required
def profile(request):
    ldap_server = "ldap://iodine-ldap.tjhsst.edu"

    base_dn = "dc=tjhsst,dc=edu"
    user_id = request.user.username
    name = ''
    kerberos_cache = request.session["KRB5CCNAME"]
    os.environ['KRB5CCNAME'] = kerberos_cache
    logger.debug("Setting KRB5CCNAME to " + kerberos_cache)

    l = ldap.initialize(ldap_server)
    auth_tokens = ldap.sasl.gssapi()
    l.sasl_interactive_bind_s('', auth_tokens)
    # print("Successfully bound to LDAP with " + l.whoami_s())
    filter = '(iodineUid=' + user_id + ')'
    # attrs = ['displayName']

    try:
        r = l.search_s(base_dn, ldap.SCOPE_SUBTREE, filter)[0][1]
    except IndexError:
        logger.error("No user " + user_id + " found in LDAP")
        # destroy(1)

    name = r['cn'][0]

    # courses = []
    # for dn in r['enrolledclass']:
    #     try:
    #         course = l.search_s(dn, ldap.SCOPE_SUBTREE)[0][1]
    #         courses.append((course['classPeriod'][0], course['cn'][0], course['roomNumber'][0]))
    #     except IndexError:
    #         "Course data incomplete"
    #         destroy(1)

    # courses = sorted(courses, key=lambda x: x[0])
    # for course in courses:
    #     print("Period {}: {}{}({})".format(course[0], course[1], " "*(25-len(course[1])), course[2]))

    return render(request, 'users/profile.html', {'foo': User.objects.return_something(), })
