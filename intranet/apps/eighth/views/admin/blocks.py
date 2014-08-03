from django.contrib import messages
from django.http import HttpResponseNotAllowed
from django.shortcuts import redirect, render
from ....auth.decorators import eighth_admin_required
from ...forms.admin.blocks import QuickAddBlockForm, BlockForm
from ...models import EighthBlock
from .general import eighth_admin_dashboard_view


@eighth_admin_required
def add_block_view(request):
    if request.method == "POST":
        form = QuickAddBlockForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully added block.")
            return redirect("eighth_admin_dashboard")
        else:
            messages.error(request, "Error adding block.")
            return eighth_admin_dashboard_view(request, add_block_form=form)
    else:
        return HttpResponseNotAllowed(["POST"])


@eighth_admin_required
def edit_block_view(request, block_id=None):
    # activity = EighthActivity.objects.get(id=activity_id)
    # if request.method == "POST":
    #     form = ActivityForm(request.POST, instance=activity)
    #     if form.is_valid():
    #         form.save()
    #         messages.success(request, "Successfully edited announcement.")
    #         return redirect("eighth_admin_dashboard")
    #     else:
    #         messages.error(request, "Error adding announcement.")
    # else:
    #     form = ActivityForm(instance=activity)

    return render(request, "eighth/admin/edit_activity.html", {"form": 123})
