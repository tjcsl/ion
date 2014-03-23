import elasticsearch
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from intranet.apps.users.models import User
from intranet import settings


@login_required
def search_view(request):
    q = request.GET.get("q", "").strip()
    if q:
        if q.isdigit():
            u = User.objects.user_with_student_id(q)
            if u is not None:
                return u

        es = elasticsearch.Elasticsearch()
        results = es.search(index="ion", body={
            "query": {
                "query_string": {
                    "query": q
                }
            }
        })
        users = [r["_source"] for r in results["hits"]["hits"]]
        return render(request, "search/search_results.html", {"search_query": q, "search_results": users})
    else:
        return render(request, "search/search_results.html", {"search_results": None})
