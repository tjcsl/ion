import logging
from io import StringIO

from django.core.management import call_command
from django.shortcuts import render

from ....auth.decorators import eighth_admin_required, reauthentication_required

logger = logging.getLogger(__name__)


@eighth_admin_required
@reauthentication_required
def index_view(request):
    context = {"admin_page_title": "Maintenance Tools"}
    return render(request, "eighth/admin/maintenance.html", context)


@eighth_admin_required
@reauthentication_required
def start_of_year_view(request):
    context = {"admin_page_title": "Start of Year Operations", "completed": False}
    if request.method == "POST" and request.POST.get("confirm"):
        try:
            content = StringIO()
            call_command("year_cleanup", run=True, confirm=True, stdout=content)
            content.seek(0)
            context["output"] = content.read()
        except Exception as e:
            # TODO: capture exception
            context["output"] = "An error occured while running the start of year scripts!\n\n{}".format(e)
        context["completed"] = True
    return render(request, "eighth/admin/start_of_year.html", context)


@eighth_admin_required
@reauthentication_required
def clear_comments_view(request):
    context = {"admin_page_title": "Clear Admin Comments", "completed": False}

    if request.method == "POST" and request.POST.get("confirm"):
        # TODO: delete admin comments when django models are made
        context["completed"] = True

    return render(request, "eighth/admin/clear_comments.html", context)
