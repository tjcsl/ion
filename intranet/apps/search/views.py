# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import elasticsearch
import re
import logging
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from ..announcements.models import Announcement
from ..events.models import Event
from ..eighth.models import EighthActivity
from ..users.models import User
from ..users.views import profile_view

logger = logging.getLogger(__name__)


def get_search_results(q):
    query_error = False
    es = elasticsearch.Elasticsearch()

    # Convert "[123 to 345]" to "[123 TO 345]"
    q = re.sub(r'\[(\d+|\*) +([Tt][Oo]) +(\d+|\*)\]', r'[\1 TO \3]', q.rstrip())

    q = re.compile(' and ', re.IGNORECASE).sub(' && ', q)
    q = re.compile(' or ', re.IGNORECASE).sub(' || ', q)
    q = re.compile('not ', re.IGNORECASE).sub(' !', q)

    def search(query):
        return es.search(index="ion", body=query, size=99999)

    query = {
        "query": {
            "multi_match": {
                "query": q,
                "fields": [
                    "ion_id",
                    "ion_username",
                    "graduation_year",
                    "common_name"
                ],
                "type": "phrase_prefix",
                "lenient": True
            }
        }
    }

    results = search(query)
    # logger.debug(results)

    if results["hits"]["total"] == 0:
        fuzzy_like_this_query = {
            "query": {
                "fuzzy_like_this": {
                    "like_text": q,
                    "fuzziness": 0.8
                }
            }
        }
        if re.match(r"^[A-Za-z0-9 ]+$", q):
            query = fuzzy_like_this_query
            results = search(query)
        else:
            query = {
                "query": {
                    "query_string": {
                        "query": q,
                        "lenient": True,
                        "allow_leading_wildcard": False
                    }
                }
            }
            try:
                results = search(query)
            except Exception as e:
                logger.debug(e)
                query_error = True
                query = fuzzy_like_this_query
                results = search(query)

    logger.debug(query)
    return query_error, results


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

        query_error, results = get_search_results(q)

        users = [r["_source"] for r in results["hits"]["hits"]]

        if is_admin:
            users = sorted(users, key=lambda u: (u["last"], u["first"]))

        """ Announcements """
        announcements_map = Announcement.es.search(q)
        announcements_ids = [a["id"] for a in announcements_map]
        announcements_all = Announcement.objects.filter(id__in=announcements_ids)
        announcements = []
        for a in announcements:
            if a.is_this_year:
                announcements.append(a)

        """ Events """
        events_map = Event.es.search(q)
        events_ids = [a["id"] for a in events_map]
        events_all = Event.objects.filter(id__in=events_ids)
        events = []
        for e in events_all:
            if e.is_this_year:
                events.append(e)

        """ Activities """
        activities_map = EighthActivity.es.search(q)
        activities_ids = [a["id"] for a in activities_map]
        activities_all = EighthActivity.objects.filter(id__in=activities_ids)
        activities = []
        only_active = (request.user.is_eighth_admin and "only_active" in request.GET) or not request.user.is_eighth_admin
        for a in activities_all:
            if (only_active and a.is_active) or not only_active:
                activities.append(a)


        if results["hits"]["total"] == 1:
            no_other_results = (not announcements and not events and not activities)
            if request.user.is_eighthoffice or no_other_results:
                user_id = results["hits"]["hits"][0]["_source"]["ion_id"]
                return redirect("user_profile", user_id=user_id)

        context = {
            "query_error": query_error,
            "search_query": q,
            "search_results": users,  # Not actual user objects
            "announcements": announcements, # Announcement objects
            "events": events, # Event objects
            "activities": activities # EighthActivity objects
        }
    else:
        context = {
            "search_results": None
        }
    context["is_admin"] = is_admin
    return render(request, "search/search_results.html", context)
