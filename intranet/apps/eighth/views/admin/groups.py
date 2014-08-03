from django.contrib import messages
from django.contrib.auth.models import Group
from django.http import HttpResponseNotAllowed
from django.shortcuts import redirect, render
from ....auth.decorators import eighth_admin_required
from ...forms.admin.groups import QuickGroupForm, GroupForm
from .general import eighth_admin_dashboard_view


@eighth_admin_required
def add_group_view(request):
    if request.method == "POST":
        form = QuickGroupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully added group.")
            return redirect("eighth_admin_dashboard")
        else:
            messages.error(request, "Error adding group.")
            return eighth_admin_dashboard_view(request, add_block_form=form)
    else:
        return HttpResponseNotAllowed(["POST"])


@eighth_admin_required
def edit_group_view(request, group_id=None):
    group = Group.objects.get(id=group_id)
    if request.method == "POST":
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully edited group.")
            return redirect("eighth_admin_dashboard")
        else:
            messages.error(request, "Error adding group.")
    else:
        form = GroupForm(instance=group)

    return render(request, "eighth/admin/edit_group.html", {"form": form})
