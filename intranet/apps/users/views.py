import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

logger = logging.getLogger(__name__)


@login_required
def profile(request):
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
    return render(request, 'users/profile.html', {'user': request.user, })
