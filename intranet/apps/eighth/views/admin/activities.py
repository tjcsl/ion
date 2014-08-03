from django.contrib import messages
from django.http import HttpResponseNotAllowed
from django.shortcuts import redirect
from ....auth.decorators import eighth_admin_required
from ...forms.admin.activities import QuickAddActivityForm, ActivityForm


@eighth_admin_required
def add_activity_view(request):
    if request.method == "POST":
        form = QuickAddActivityForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully added announcement.")
        else:
            messages.error(request, "Error adding announcement.")
        return redirect("eighth_admin_dashboard")
    else:
        return HttpResponseNotAllowed(["POST"])
