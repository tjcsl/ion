import cPickle
from django.contrib import messages
from django.contrib.auth.models import Group
from django.contrib.formtools.wizard.views import SessionWizardView
from django.shortcuts import render, redirect
from ....auth.decorators import eighth_admin_required
from ...forms.admin import (
    activities as activity_forms, blocks as block_forms, groups as group_forms,
    rooms as room_forms, sponsors as sponsor_forms)
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

    context = {
        "start_date": start_date,
        "all_activities": all_activities,
        "blocks_after_start_date": blocks_after_start_date,
        "groups": groups,
        "rooms": rooms,
        "sponsors": sponsors,

        # Used in place of IDs in data-href-pattern tags of .dynamic-links
        # to reverse single-ID urls in Javascript. It's rather hacky, but
        # not unlike boundaries of multipart/form-data requests, so it's
        # not completely invalid. If there's a better way to do this,
        # please implement it.
        "url_id_placeholder": "734784857438457843756435654645642343465"
    }

    forms = {
        "add_activity_form": activity_forms.QuickActivityForm,
        "add_block_form": block_forms.QuickBlockForm,
        "add_group_form": group_forms.QuickGroupForm,
        "add_room_form": room_forms.RoomForm

    }

    for form_name, form_class in forms.items():
        form_css_id = form_name.replace("_", "-")

        if form_name in kwargs:
            context[form_name] = kwargs.get(form_name)
            context["scroll_to_id"] = form_css_id
        elif form_name in request.session:
            pickled_form = request.session.pop(form_name)
            context[form_name] = cPickle.loads(str(pickled_form))
            context["scroll_to_id"] = form_css_id
        else:
            context[form_name] = form_class()

    return render(request, "eighth/admin/dashboard.html", context)


@eighth_admin_required
def not_implemented_view(request, *args, **kwargs):
    raise NotImplementedError("This view has not been implemented yet.")


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
