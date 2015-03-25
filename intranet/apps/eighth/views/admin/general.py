# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import cPickle
from urllib import unquote
from django.contrib import messages
from django.contrib.auth.models import Group
from django.shortcuts import render, redirect
from ....auth.decorators import eighth_admin_required
from ...forms.admin import (
    activities as activity_forms, blocks as block_forms, groups as group_forms,
    rooms as room_forms, sponsors as sponsor_forms, general as general_forms)
from ...models import EighthActivity, EighthBlock, EighthRoom, EighthSponsor
from ...utils import get_start_date, set_start_date


@eighth_admin_required
def eighth_admin_dashboard_view(request, **kwargs):
    start_date = get_start_date(request)
    all_activities = EighthActivity.undeleted_objects.order_by("name")
    blocks_after_start_date = (EighthBlock.objects
                                          .filter(date__gte=start_date)
                                          .order_by("date"))
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

        "admin_page_title": "Eighth Period Admin",

        # Used in place of IDs in data-href-pattern tags of .dynamic-links
        # to reverse single-ID urls in Javascript. It's rather hacky, but
        # not unlike boundaries of multipart/form-data requests, so it's
        # not completely bad. If there's a better way to do this,
        # please implement it.
        "url_id_placeholder": "734784857438457843756435654645642343465"
    }

    forms = {
        "add_activity_form": activity_forms.QuickActivityForm,
        "add_block_form": block_forms.QuickBlockForm,
        "add_group_form": group_forms.QuickGroupForm,
        "add_room_form": room_forms.RoomForm,
        "add_sponsor_form": sponsor_forms.SponsorForm
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
def edit_start_date_view(request):
    if request.method == "POST":
        form = general_forms.StartDateForm(request.POST)
        if form.is_valid():
            new_start_date = form.cleaned_data["date"]
            set_start_date(request, new_start_date)
            messages.success(request, "Successfully changed start date")

            redirect_destination = "eighth_admin_dashboard"
            if "next_page" in request.GET:
                redirect_destination = unquote(request.GET["next_page"])

            return redirect(redirect_destination)
        else:
            messages.error(request, "Error changing start date.")
    else:
        initial_data = {
            "date": get_start_date(request)
        }
        form = general_forms.StartDateForm(initial=initial_data)

    context = {
        "form": form,
        "admin_page_title": "Change Start Date"
    }
    return render(request, "eighth/admin/edit_start_date.html", context)


@eighth_admin_required
def not_implemented_view(request, *args, **kwargs):
    raise NotImplementedError("This view has not been implemented yet.")
