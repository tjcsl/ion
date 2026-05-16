from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import render

from .stats import build_wrapped_context


@login_required
def wrapped_view(request):
    if not settings.ENABLE_ION_WRAPPED:
        raise Http404

    if not request.user.is_student:
        return HttpResponseForbidden("Ion Wrapped is only available for students.")

    return render(request, "wrapped/wrapped.html", build_wrapped_context(request.user))
