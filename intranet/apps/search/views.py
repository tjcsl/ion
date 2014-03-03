from django.shortcuts import render
from intranet import settings


def search_view(request):
    q = request.GET.get("q", "").strip()
    if q:
        if q.isdigit() and len(q) == settings.FCPS_STUDENT_ID_LENGTH:
            pass

        return render(request, "search/search_results.html", {"search_query": q})
    else:
        return render(request, "search/search_results.html", {"search_query": "No results"})
