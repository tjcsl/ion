import os
import logging
from intranet.apps.dashboard.views import dashboard_view
from .forms import AuthenticateForm
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.views.generic.base import View

logger = logging.getLogger(__name__)


def index(request, auth_form=None):
    if request.user.is_authenticated():
        return dashboard_view(request)
    else:
        auth_form = auth_form or AuthenticateForm()
        return render(request,
                      'auth/login.html',
                      {'auth_form': auth_form, })


class login_view(View):
    def post(self, request):
        form = AuthenticateForm(data=request.POST)

        if form.is_valid():
            login(request, form.get_user())
            # Initial load into session
            request.session["KRB5CCNAME"] = os.environ['KRB5CCNAME']

            next = request.GET.get("next", "/")
            return redirect(next)
        else:
            logger.info("Login failed")
            return index(request, auth_form=form)  # Modified to show errors
    def get(self, request):
        return index(request)


def logout_view(request):
    try:
        kerberos_cache = request.session["KRB5CCNAME"]
        os.system("/usr/bin/kdestroy -c " + kerberos_cache)
    except KeyError:
        pass
    logger.info("Destroying kerberos cache and logging out")
    logout(request)
    return redirect("/")
