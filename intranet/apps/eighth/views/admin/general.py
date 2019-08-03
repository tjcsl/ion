from urllib.parse import unquote

from cacheops import invalidate_all

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.shortcuts import redirect, render
from django.utils import timezone

from ....auth.decorators import eighth_admin_required
from ....groups.models import Group
from ...forms.admin import general as general_forms
from ...forms.admin import groups as group_forms
from ...forms.admin import rooms as room_forms
from ...models import EighthActivity, EighthBlock, EighthRoom, EighthScheduledActivity, EighthSignup, EighthSponsor
from ...utils import get_start_date, set_start_date


@eighth_admin_required
def eighth_admin_dashboard_view(request, **kwargs):
    start_date = get_start_date(request)
    all_activities = EighthActivity.objects.order_by("name").only(
        "id", "name", "special", "restricted", "both_blocks", "administrative", "sticky", "deleted"
    )  # show deleted activities
    blocks_after_start_date = EighthBlock.objects.filter(date__gte=start_date).order_by("date")

    next_block_after_start_date = blocks_after_start_date.first()
    if next_block_after_start_date is None:
        blocks_next = EighthBlock.objects.none()
        blocks_next_date = None
    else:
        blocks_next_date = next_block_after_start_date.date
        blocks_next = EighthBlock.objects.filter(date=blocks_next_date)

    groups = Group.objects.prefetch_related("groupproperties").annotate(user_count=Count("user")).order_by("name")
    rooms = EighthRoom.objects.all()
    sponsors = (
        EighthSponsor.objects.select_related("user")
        .only("id", "last_name", "first_name", "show_full_name", "user__id")
        .order_by("last_name", "first_name")
    )

    signup_users_count = get_user_model().objects.get_students().count()

    context = {
        "start_date": start_date,
        "all_activities": all_activities,
        "blocks_after_start_date": blocks_after_start_date,
        "groups": groups,
        "rooms": rooms,
        "sponsors": sponsors,
        "blocks_next": blocks_next,
        "blocks_next_date": blocks_next_date,
        "signup_users_count": signup_users_count,
        "admin_page_title": "Eighth Period Admin",
        # Used in place of IDs in data-href-pattern tags of .dynamic-links
        # to reverse single-ID urls in Javascript. It's rather hacky, but
        # not unlike boundaries of multipart/form-data requests, so it's
        # not completely bad. If there's a better way to do this,
        # please implement it.
        "url_id_placeholder": "734784857438457843756435654645642343465",
    }

    forms = {"add_group_form": group_forms.QuickGroupForm, "add_room_form": room_forms.RoomForm}

    for form_name, form_class in forms.items():
        form_css_id = form_name.replace("_", "-")

        if form_name in kwargs:
            context[form_name] = kwargs.get(form_name)
            context["scroll_to_id"] = form_css_id
        elif form_name in request.session:
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
        initial_data = {"date": get_start_date(request)}
        form = general_forms.StartDateForm(initial=initial_data)

    context = {"form": form, "admin_page_title": "Change Start Date"}
    return render(request, "eighth/admin/edit_start_date.html", context)


# TODO: UserCache
@eighth_admin_required
def cache_view(request):
    if request.method == "POST":
        if "invalidate_all" in request.POST:
            invalidate_all()
            messages.success(request, "Invalidated all of the cache")

    try:
        opts = settings.CACHEOPS
        default = settings.CACHEOPS_DEFAULTS
    except AttributeError:
        opts = default = None

    cache = {}
    if opts:
        for ctype in opts:
            c = ctype.split(".", 1)[0]
            if "timeout" in opts[ctype]:
                to = opts[ctype]["timeout"]
            else:
                to = default["timeout"]
            cache[c] = int(to / (60 * 60))

    context = {"admin_page_title": "Cache Configuration", "cache_length": cache}
    return render(request, "eighth/admin/cache.html", context)


@eighth_admin_required
def history_view(request):
    history_timeframe = timezone.localtime() - timezone.timedelta(minutes=15)
    history = {
        "EighthSignup": EighthSignup.history.filter(history_date__gt=history_timeframe),  # pylint: disable=no-member
        "EighthScheduledActivity": EighthScheduledActivity.history.filter(history_date__gt=history_timeframe),  # pylint: disable=no-member
        "EighthActivity": EighthActivity.history.filter(history_date__gt=history_timeframe),  # pylint: disable=no-member
        "EighthBlock": EighthBlock.history.filter(history_date__gt=history_timeframe),  # pylint: disable=no-member
    }
    context = {"history": history, "admin_page_title": "Event History"}
    return render(request, "eighth/admin/history.html", context)
