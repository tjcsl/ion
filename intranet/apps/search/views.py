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

    if q:

        if q.isdigit():
            # Match exact student ID if the input looks like an ID
            u = User.objects.user_with_student_id(q)
            if u is not None:
                return profile_view(request, user_id=u.id)

        es = elasticsearch.Elasticsearch()

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
                    "type": "phrase",
                    "lenient": True
                }
            }
        }

        results = search(query)
        num_results = results["hits"]["total"]

        if num_results == 0:
            fuzzy_like_this_query = {
                "query": {
                    "fuzzy_like_this": {
                        "like_text": q,
                        "fuzziness": 0.8
                    }
                }
            }
            if re.match(r"^[A-Za-z0-9 ]+$", q):
                results = search(fuzzy_like_this_query)
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
                    results = search(fuzzy_like_this_query)

        logger.debug(query)
        if num_results == 1:
            user_id = results["hits"]["hits"][0]["_source"]["ion_id"]
            return redirect("user_profile", user_id=user_id)

        users = [r["_source"] for r in results["hits"]["hits"]]
        context = {
            "query_error": query_error,
            "search_query": q,
            "search_results": users  # Not actual user objects
        }
    else:
        context = {
            "search_results": None
        }
    return render(request, "search/search_results.html", context)
