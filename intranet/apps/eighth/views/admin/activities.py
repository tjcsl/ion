# pylint: disable=too-many-boolean-expressions
import logging
import pickle

from cacheops import invalidate_obj

from django import forms, http
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse

from ....auth.decorators import eighth_admin_required
from ....groups.models import Group
from ...forms.admin.activities import ActivityForm, QuickActivityForm
from ...models import EighthActivity, EighthRoom, EighthScheduledActivity, EighthSponsor, EighthWaitlist
from ...tasks import room_changed_activity_email
from ...utils import get_start_date

logger = logging.getLogger(__name__)


@eighth_admin_required
def add_activity_view(request):
    if request.method == "POST":
        form = QuickActivityForm(request.POST)
        if form.is_valid():
            new_id = request.POST.get("id", "default")
            if new_id == "default":
                activity = form.save()
            else:
                activity = EighthActivity.objects.create(name=form.cleaned_data["name"], id=int(new_id))
            invalidate_obj(activity)
            messages.success(request, "Successfully added activity.")
            return redirect("eighth_admin_edit_activity", activity_id=activity.id)
        else:
            messages.error(request, "Error adding activity.")
            request.session["add_activity_form"] = pickle.dumps(form)
            return redirect("eighth_admin_dashboard")
    else:
        context = {"admin_page_title": "Add Activity", "form": QuickActivityForm(), "available_ids": EighthActivity.available_ids()}
        return render(request, "eighth/admin/add_activity.html", context)


@eighth_admin_required
def edit_activity_view(request, activity_id):
    try:
        activity = EighthActivity.objects.get(id=activity_id)  # include deleted
    except EighthActivity.DoesNotExist:
        raise http.Http404

    if request.method == "POST":
        form = ActivityForm(request.POST, instance=activity)
        if form.is_valid():
            try:

                # Check if sponsor change
                old_sponsors = activity.sponsors.all()
                old_sponsor_ids = old_sponsors.values_list("id", flat=True)
                new_sponsor_ids = [s.id for s in form.cleaned_data["sponsors"]]

                if set(old_sponsor_ids) != set(new_sponsor_ids) and old_sponsor_ids:
                    start_date = get_start_date(request)
                    sched_acts_default = EighthScheduledActivity.objects.filter(activity=activity, sponsors=None, block__date__lt=start_date)

                    if sched_acts_default.count() > 0:
                        # This will change scheduled activities that used overrides in the past.
                        # Thus, by looping through the scheduled activities that didn't have any
                        # custom sponsors specified, we *could* prevent anything from visibly
                        # changing by making an override with the value of the previous default.

                        # Yes: Save History => Override old values
                        # No: Change Globally => Don't override old values, they will change to new default

                        if "change_sponsor_history" in request.POST:
                            change = request.POST.get("change_sponsor_history")

                            if change == "yes":
                                # Override old entries
                                for sa in sched_acts_default:
                                    for sponsor in old_sponsors:
                                        sa.sponsors.add(sponsor)
                                    sa.save()
                                messages.success(
                                    request, "Overrode {} scheduled activities to old sponsor default".format(sched_acts_default.count())
                                )
                            elif change == "no":
                                # Don't override
                                messages.success(request, "Changing default sponsors globally")
                                # Continues to form.save()
                        else:
                            # show message, asking whether to change history
                            context = {
                                "admin_page_title": "Keep Sponsor History?",
                                "activity": activity,
                                "sched_acts_count": sched_acts_default.count(),
                                "start_date": start_date,
                                "old_sponsors": EighthSponsor.objects.filter(id__in=old_sponsor_ids),
                                "new_sponsors": EighthSponsor.objects.filter(id__in=new_sponsor_ids),
                                "form": form,
                            }
                            return render(request, "eighth/admin/keep_sponsor_history.html", context)
                    else:
                        messages.success(request, "You modified the default sponsors, but those changes will not affect any scheduled activities.")

                # Check if room change
                old_rooms = activity.rooms.all()
                old_room_ids = old_rooms.values_list("id", flat=True)
                new_room_ids = [r.id for r in form.cleaned_data["rooms"]]

                if set(old_room_ids) != set(new_room_ids) and old_room_ids:
                    start_date = get_start_date(request)
                    sched_acts_default = EighthScheduledActivity.objects.filter(activity=activity, rooms=None, block__date__lt=start_date)

                    if sched_acts_default.count() > 0:
                        # This will change scheduled activities that used overrides in the past.
                        # Thus, by looping through the scheduled activities that didn't have any
                        # custom rooms specified, we *could* prevent anything from visibly
                        # changing by making an override with the value of the previous default.

                        # Yes: Save History => Override old values
                        # No: Change Globally => Don't override old values, they will change to new default

                        if "change_room_history" in request.POST:
                            change = request.POST.get("change_room_history")

                            if change == "yes":
                                # Override old entries
                                for sa in sched_acts_default:
                                    sa.rooms.set(old_rooms)
                                messages.success(request, "Overrode {} scheduled activities to old room default".format(sched_acts_default.count()))
                            elif change == "no":
                                # Don't override
                                messages.success(request, "Changing default rooms globally")
                                # Continues to form.save()
                        else:
                            # show message, asking whether to change history
                            context = {
                                "admin_page_title": "Keep Room History?",
                                "activity": activity,
                                "sched_acts_count": sched_acts_default.count(),
                                "start_date": start_date,
                                "old_rooms": EighthRoom.objects.filter(id__in=old_room_ids),
                                "new_rooms": EighthRoom.objects.filter(id__in=new_room_ids),
                                "form": form,
                            }
                            return render(request, "eighth/admin/keep_room_history.html", context)
                    else:
                        messages.success(request, "You modified the default rooms, but those changes will not affect any scheduled activities.")

                if set(old_room_ids) != set(new_room_ids):
                    # Notify people that the activities they're signed up for have changed rooms
                    room_changed_activity_email.delay(activity, old_rooms, EighthRoom.objects.filter(id__in=new_room_ids))

                form.save()
            except forms.ValidationError as error:
                error = str(error)
                messages.error(request, error)
            else:
                if (
                    activity.restricted
                    or activity.one_a_day
                    or activity.presign
                    or activity.both_blocks
                    or activity.sticky
                    or activity.administrative
                ):
                    all_sched_acts = EighthScheduledActivity.objects.filter(activity=activity)
                    for sa in all_sched_acts:
                        EighthWaitlist.objects.filter(scheduled_activity=sa).delete()
                messages.success(request, "Successfully edited activity.")
                if "add_group" in request.POST:
                    grp_name = "Activity: {}".format(activity.name)
                    grp, status = Group.objects.get_or_create(name=grp_name)
                    activity.restricted = True
                    activity.groups_allowed.add(grp)
                    activity.save()
                    invalidate_obj(activity)
                    messages.success(request, "{} to '{}' group".format("Created and added" if status else "Added", grp_name))
                    return redirect("eighth_admin_edit_group", grp.id)

                return redirect("eighth_admin_edit_activity", activity_id)
        else:
            messages.error(request, "Error adding activity.")
    else:
        form = ActivityForm(instance=activity)

    activities = EighthActivity.undeleted_objects.order_by("name")

    activity_groups = []
    for g in activity.groups_allowed.all():
        group = {}
        group["id"] = g.id
        group["name"] = "{}".format(g)
        group["members_alpha"] = sorted(g.user_set.all(), key=lambda x: (x.last_name, x.first_name))
        group["members_alpha_count"] = len(group["members_alpha"])
        activity_groups.append(group)

    activity_members = sorted(activity.users_allowed.all(), key=lambda x: (x.last_name, x.first_name))
    context = {
        "form": form,
        "admin_page_title": "Edit Activity",
        "delete_url": reverse("eighth_admin_delete_activity", args=[activity_id]),
        "activity": activity,
        "activity_groups": activity_groups,
        "activities": activities,
        "activity_members": activity_members,
    }

    return render(request, "eighth/admin/edit_activity.html", context)


@eighth_admin_required
def delete_activity_view(request, activity_id=None):
    try:
        activity = EighthActivity.objects.get(id=activity_id)
    except EighthActivity.DoesNotExist:
        raise http.Http404

    perm_delete = False
    if activity.deleted and "perm" in request.GET:
        perm_delete = True

    if request.method == "POST":
        if perm_delete:
            activity.delete()
        else:
            activity.deleted = True
            activity.save()
            invalidate_obj(activity)
        messages.success(request, "Successfully deleted activity.")
        return redirect("eighth_admin_dashboard")
    else:
        context = {
            "admin_page_title": "Delete Activity",
            "item_name": activity.name,
            "help_text": (
                "Deleting will not destroy past attendance data for this "
                "activity. The activity will just be marked as deleted "
                "and hidden from non-attendance views."
                if not perm_delete
                else "This will destroy past attendance data."
            ),
        }

        return render(request, "eighth/admin/delete_form.html", context)
