# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import elasticsearch
import re
import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from ..users.models import User
from ..users.views import profile_view

logger = logging.getLogger(__name__)


@login_required
def search_view(request):
    q = request.GET.get("q", "").strip()
    query_error = False
    is_admin = request.user.is_teacher and request.user.is_eighth_admin

    if q:

        if q.isdigit():
            # Match exact student ID if the input looks like an ID
            u = User.objects.user_with_student_id(q)
            if u is not None:
                return profile_view(request, user_id=u.id)

        es = elasticsearch.Elasticsearch()

        # Convert "[123 to 345]" to "[123 TO 345]"
        q = re.sub(r'\[(\d+|\*) +([Tt][Oo]) +(\d+|\*)\]', r'[\1 TO \3]', q.rstrip())


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
        if results["hits"]["total"] == 1:
            user_id = results["hits"]["hits"][0]["_source"]["ion_id"]
            return redirect("user_profile", user_id=user_id)

        users = [r["_source"] for r in results["hits"]["hits"]]

        if is_admin:
            users = sorted(users, key=lambda u: (u["last"], u["first"]))

        context = {
            "query_error": query_error,
            "search_query": q,
            "search_results": users  # Not actual user objects
        }
    else:
        context = {
            "search_results": None
        }
    context["is_admin"] = is_admin
    return render(request, "search/search_results.html", context)
