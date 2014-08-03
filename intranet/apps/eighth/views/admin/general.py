from django.contrib import messages
from django.contrib.auth.models import Group
from django.contrib.formtools.wizard.views import SessionWizardView
from django.shortcuts import render, redirect
from ....auth.decorators import eighth_admin_required
from ...forms.admin import (
    activities as activity_forms, blocks as block_forms, rooms as room_forms,
    sponsors as sponsor_forms)
from ...models import EighthActivity, EighthBlock, EighthRoom, EighthSponsor
from ...utils import get_start_date


@eighth_admin_required
def eighth_admin_dashboard_view(request, **kwargs):
    start_date = get_start_date(request)
    all_activities = EighthActivity.objects.order_by("name")
    blocks_after_start_date = EighthBlock.objects.filter(date__gte=start_date)\
                                                 .order_by("date")
    groups = Group.objects.order_by("name")
    rooms = EighthRoom.objects.all()
    sponsors = EighthSponsor.objects.order_by("last_name", "first_name")

    forms = {
        "add_activity_form": activity_forms.QuickAddActivityForm,

    }

    context = {
        "start_date": start_date,
        "all_activities": all_activities,
        "blocks_after_start_date": blocks_after_start_date,
        "groups": groups,
        "rooms": rooms,
        "sponsors": sponsors,
    }

    for form_name, form_class in forms.items():
        context[form_name] = kwargs.get(form_name, form_class())

    return render(request, "eighth/admin/dashboard.html", context)


class EighthAdminExampleWizard(SessionWizardView):
    FORMS = [
        ("block", block_forms.BlockSelectionForm),
        ("activity", activity_forms.ActivitySelectionForm)
    ]

    TEMPLATES = {
        "block": "eighth/admin/example_form.html",
        "activity": "eighth/admin/example_form.html"
    }

    def get_template_names(self):
        return [self.TEMPLATES[self.steps.current]]

    def get_form_kwargs(self, step):
        kwargs = {}
        if step == "activity":
            block = self.get_cleaned_data_for_step("block")["block"]
            kwargs.update({"block": block})
        return kwargs

    def done(self, form_list, **kwargs):
        messages.info(self.request, "Successfully did something")

        return redirect("eighth_admin_index")
