# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import elasticsearch
import re
import logging
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from intranet.db.ldap_db import LDAPConnection
from ..announcements.models import Announcement
from ..events.models import Event
from ..eighth.models import EighthActivity
from ..users.models import User
from ..users.views import profile_view

logger = logging.getLogger(__name__)


def do_ldap_query(q):
    c = LDAPConnection()
    result_dns = []

    if q.isdigit():
        query = "(&(|(tjhsstStudentId={0})(iodineUidNumber={0}))(objectClass=*))".format(q)
        res = c.search(settings.USER_DN, query, [])
        for row in res:
            dn = row[0]
            result_dns.append(dn)
    else:
        parts = q.split(" ")

        i = 0
        for p in parts:
            query = ("(&(|(givenName=*{0})"
                     "(givenName={0}*)"
                     "(sn=*{0})"
                     "(sn={0}*)"
                     "(iodineUid=*{0})"
                     "(iodineUid={0}*)"
                     "(mname=*{0})"
                     "(mname={0}*)"
                     "(nickname=*{0})"
                     "(nickname={0}*)"
                     ")(objectClass=*))".format(p))

            res = c.search(settings.USER_DN, query, [])
            new_dns = []
            for row in res:
                dn = row[0]
                if i == 0:
                    new_dns.append(dn)
                elif dn in result_dns:
                    new_dns.append(dn)

            result_dns = new_dns
            i += 1

    users = []
    for dn in result_dns:
        user = User.get_user(dn=dn)
        users.append(user)

    return users


def get_search_results(q):
    query_error = False

    users = do_ldap_query(q)

    return False, users


@login_required
def search_view(request):
    q = request.GET.get("q", "").strip()
    is_admin = (not request.user.is_student and request.user.is_eighth_admin)

    if q:
        """ User search """
        if q.isdigit() and (len(str(q)) == settings.FCPS_STUDENT_ID_LENGTH):
            # Match exact student ID if the input looks like an ID
            u = User.objects.user_with_student_id(q)
            if u is not None:
                return profile_view(request, user_id=u.id)

        query_error, users = get_search_results(q)

        if is_admin:
            users = sorted(users, key=lambda u: (u.last_name, u.first_name))

        """
        # Announcements
        announcements_map = Announcement.es.search(q)
        announcements_ids = [a["id"] for a in announcements_map]
        announcements_all = Announcement.objects.filter(id__in=announcements_ids)
        announcements = []
        for a in announcements:
            if a.is_this_year:
                announcements.append(a)

        # Events
        events_map = Event.es.search(q)
        events_ids = [a["id"] for a in events_map]
        events_all = Event.objects.filter(id__in=events_ids)
        events = []
        for e in events_all:
            if e.is_this_year:
                events.append(e)

        # Activities
        activities_map = EighthActivity.es.search(q)
        activities_ids = [a["id"] for a in activities_map]
        activities_all = EighthActivity.objects.filter(id__in=activities_ids)
        activities = []
        only_active = (request.user.is_eighth_admin and "only_active" in request.GET) or not request.user.is_eighth_admin
        for a in activities_all:
            if (only_active and a.is_active) or not only_active:
                activities.append(a)
        """

        if len(users) == 1:
            no_other_results = True  # (not announcements and not events and not activities)
            if request.user.is_eighthoffice or no_other_results:
                user_id = users[0].id
                return redirect("user_profile", user_id=user_id)

        context = {
            "query_error": query_error,
            "search_query": q,
            "search_results": users,  # Not actual user objects
            #"announcements": announcements, # Announcement objects
            #"events": events, # Event objects
            #"activities": activities # EighthActivity objects
        }
    else:
        context = {
            "search_results": None
        }
    context["is_admin"] = is_admin
    return render(request, "search/search_results.html", context)
