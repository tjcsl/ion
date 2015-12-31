# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from ldap3.utils.conv import escape_filter_chars
from intranet.db.ldap_db import LDAPConnection
from ..announcements.models import Announcement
from ..events.models import Event
from ..eighth.models import EighthActivity
from ..search.utils import get_query
from ..users.models import User, Grade
from ..users.views import profile_view

logger = logging.getLogger(__name__)


def do_ldap_query(q, admin=False):
    c = LDAPConnection()
    result_dns = []

    q = escape_filter_chars(q)
    # Allow wildcards
    q = q.replace(escape_filter_chars('*'), '*')

    # If only a digit, search for student ID and user ID
    if q.isdigit():
        logger.debug("Digit search: {}".format(q))
        query = ("(&(|(tjhsstStudentId={0})"
                 "(iodineUidNumber={0})"
                 ")(|(objectClass=tjhsstStudent)(objectClass=tjhsstTeacher)))").format(q)

        logger.debug("Running LDAP query: {}".format(query))

        res = c.search(settings.USER_DN, query, [])
        for row in res:
            dn = row[0]
            result_dns.append(dn)
    elif ":" in q:
        logger.debug("Advanced search")
        # A mapping between search keys and LDAP entires
        map_attrs = {
            "firstname": ("givenname", "nickname",),
            "first": ("givenname", "nickname",),
            "lastname": ("sn",),
            "last": ("sn",),
            "nick": ("nickname",),
            "nickname": ("nickname",),
            "name": ("sn", "mname", "givenname", "nickname",),
            "city": ("l",),
            "town": ("l",),
            "middlename": ("mname",),
            "middle": ("mname",),
            "phone": ("homephone", "mobile",),
            "homephone": ("homephone",),
            "cell": ("mobile",),
            "address": ("street",),
            "zip": ("postalcode",),
            "grade": ("graduationYear",),
            "gradyear": ("graduationYear",),
            "email": ("mail",),
            "studentid": ("tjhsstStudentId",),
            "sex": ("sex",),
            "gender": ("sex",),
            "id": ("iodineUidNumber",),
            "username": ("iodineUid",),
            "counselor": ("counselor",),
            "type": ("objectClass",)
        }

        inner = ""
        parts = q.split(" ")
        # split each word
        for p in parts:
            # Check for less than/greater than, and replace =
            sep = "="
            if ":" in p:
                cat, val = p.split(":")
            elif "=" in p:
                cat, val = p.split("=")
            elif "<" in p:
                cat, val = p.split("<")
                sep = "<="
            elif ">" in p:
                cat, val = p.split(">")
                sep = ">="
            else:
                logger.debug("Advanced fallback: {}".format(p))
                # Fall back on regular searching (there's no key)

                # Wildcards are already implied at the start and end
                if p.endswith("*"):
                    p = p[:-1]
                if p.startswith("*"):
                    p = p[1:]

                exact = False
                if p.startswith('"') and p.endswith('"'):
                    exact = True
                    p = p[1:-1]

                if len(p) == 0:
                    continue

                if exact:
                    # No implied wildcard
                    inner += (("(|(givenName={0})"
                               "(sn={0})"
                               "(iodineUid={0})") +
                              ("(mname={0})" if admin else "") +
                              ("(nickname={0})"
                               ")")).format(p)
                else:
                    # Search firstname, lastname, uid, nickname (+ middlename if admin) with
                    # implied wildcard at beginning and end of the search string
                    inner += (("(|(givenName=*{0})"
                               "(givenName={0}*)"
                               "(sn=*{0})"
                               "(sn={0}*)"
                               "(iodineUid=*{0})"
                               "(iodineUid={0}*)") +
                              ("(mname=*{0})"
                               "(mname={0}*)" if admin else "") +
                              ("(nickname=*{0})"
                               "(nickname={0}*)"
                               ")")).format(p)

                continue  # skip rest of processing
            logger.debug("Advanced exact: {}".format(p))
            if val.startswith('"') and val.endswith('"'):
                # Already exact
                val = val[1:-1]

            cat = cat.lower()
            val = val.lower()

            # fix grade, because LDAP only stores graduation year
            if cat == "grade" and val.isdigit():
                val = "{}".format(Grade.year_from_grade(int(val)))
            elif cat == "grade" and val == "staff":
                cat = "type"
                val = "teacher"
            elif cat == "grade" and val == "student":
                cat = "type"
                val = "student"

            if cat == "type" and val == "teacher":
                val = "tjhsstTeacher"
            elif cat == "type" and val == "student":
                val = "tjhsstStudent"

            # replace sex:male with sex:m and sex:female with sex:f
            if cat == "sex" or cat == "gender":
                val = val[:1]

            # if an invalid key, ignore
            if cat not in map_attrs:
                continue

            attrs = map_attrs[cat]

            inner += "(|"
            # for each of the possible LDAP fields, add to the search query
            for attr in attrs:
                inner += "({}{}{})".format(attr, sep, val)
            inner += ")"

        query = "(&{}(|(objectClass=tjhsstStudent)(objectClass=tjhsstTeacher)))".format(inner)

        logger.debug("Running LDAP query: {}".format(query))

        res = c.search(settings.USER_DN, query, [])
        for row in res:
            dn = row[0]
            result_dns.append(dn)

    else:
        logger.debug("Simple search")
        # Non-advanced search; no ":"
        parts = q.split(" ")
        # split on each word
        i = 0
        for p in parts:
            exact = False
            logger.debug(p)
            if p.startswith('"') and p.endswith('"'):
                exact = True
                p = p[1:-1]

            if exact:
                logger.debug("Simple exact: {}".format(p))
                # No implied wildcard
                query = (("(&(|(givenName={0})"
                          "(sn={0})"
                          "(iodineUid={0})") +
                         ("(mname={0})" if admin else "") +
                         ("(nickname={0})"
                          ")(|(objectClass=tjhsstStudent)(objectClass=tjhsstTeacher)))")).format(p)
            else:
                logger.debug("Simple wildcard: {}".format(p))
                if p.endswith("*"):
                    p = p[:-1]
                if p.startswith("*"):
                    p = p[1:]
                # Search for first, last, middle, nickname uid, with implied
                # wildcard at beginning and end
                query = (("(&(|(givenName=*{0})"
                          "(givenName={0}*)"
                          "(sn=*{0})"
                          "(sn={0}*)"
                          "(iodineUid=*{0})"
                          "(iodineUid={0}*)") +
                         ("(mname=*{0})"
                          "(mname={0}*)" if admin else "") +
                         ("(nickname=*{0})"
                          "(nickname={0}*)"
                          ")(|(objectClass=tjhsstStudent)(objectClass=tjhsstTeacher)))")).format(p)

            logger.debug("Running LDAP query: {}".format(query))

            res = c.search(settings.USER_DN, query, ["dn"])
            new_dns = []
            # if multiple words, delete those that weren't in previous searches
            for row in res:
                dn = row["dn"]
                if i == 0:
                    new_dns.append(dn)
                elif dn in result_dns:
                    new_dns.append(dn)

            result_dns = new_dns
            i += 1

    # loop through the DNs saved and get actual user objects
    users = []
    for dn in result_dns:
        user = User.get_user(dn=dn)
        users.append(user)

    return users


def get_search_results(q, admin=False):
    try:
        q = q.replace("+", " ")
        if str == bytes:
            # python 2 only
            q = q.encode("utf-8")
        users = []

        queries = q.split(" OR ")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return True, []

    for qu in queries:
        users += do_ldap_query(qu, admin)

    return False, users


def do_activities_search(q):
    filter_query = get_query(q, ["name", "description"])
    entires = EighthActivity.objects.filter(filter_query).order_by("name")
    final_entires = []
    for e in entires:
        if e.is_active:
            final_entires.append(e)
    return final_entires


def do_announcements_search(q):
    filter_query = get_query(q, ["title"])
    entires = Announcement.objects.filter(filter_query).order_by("title")
    final_entires = []
    for e in entires:
        if e.is_this_year:
            final_entires.append(e)
    return final_entires


def do_events_search(q):
    filter_query = get_query(q, ["title"])
    entires = Event.objects.filter(filter_query).order_by("title")
    final_entires = []
    for e in entires:
        if e.is_this_year:
            final_entires.append(e)
    return final_entires


@login_required
def search_view(request):
    q = request.GET.get("q", "").strip()
    is_admin = (not request.user.is_student and request.user.is_eighthoffice)

    if q:
        """ User search """
        if q.isdigit() and (len(str(q)) == settings.FCPS_STUDENT_ID_LENGTH):
            # Match exact student ID if the input looks like an ID
            u = User.objects.user_with_student_id(q)
            if u is not None:
                return profile_view(request, user_id=u.id)

        query_error, users = get_search_results(q, request.user.is_eighthoffice)

        if is_admin:
            users = sorted(users, key=lambda u: (u.last_name, u.first_name))

        activities = do_activities_search(q)
        announcements = do_announcements_search(q)
        events = do_events_search(q)

        logger.debug(activities)
        logger.debug(announcements)
        logger.debug(events)

        if len(users) == 1:
            no_other_results = (not activities and not announcements)
            if request.user.is_eighthoffice or no_other_results:
                user_id = users[0].id
                return redirect("user_profile", user_id=user_id)

        context = {
            "query_error": query_error,
            "search_query": q,
            "search_results": users,  # User objects
            "announcements": announcements,  # Announcement objects
            "events": events,  # Event objects
            "activities": activities  # EighthActivity objects
        }
    else:
        context = {
            "search_results": None
        }
    context["is_admin"] = is_admin
    return render(request, "search/search_results.html", context)
