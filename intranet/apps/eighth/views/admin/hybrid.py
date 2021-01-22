import logging

from django.contrib import messages
from django.shortcuts import redirect, render

from ....auth.decorators import eighth_admin_required
from ...models import EighthBlock, EighthScheduledActivity, EighthSignup, EighthSponsor
from ...utils import get_start_date

logger = logging.getLogger(__name__)


@eighth_admin_required
def activities_without_attendance_view(request):
    blocks_set = set()
    for b in EighthBlock.objects.filter(
        eighthscheduledactivity__in=EighthScheduledActivity.objects.filter(activity__name="z - Hybrid Sticky")
    ).filter(date__gte=get_start_date(request)):
        blocks_set.add((str(b.date), b.block_letter[0]))
    blocks = sorted(list(blocks_set))

    block_id = request.GET.get("block", None)
    block = None

    if block_id is not None:
        try:
            block_id = tuple(block_id.split(","))
            block = EighthBlock.objects.filter(date=block_id[0], block_letter__contains=block_id[1])
        except (EighthBlock.DoesNotExist, ValueError):
            pass

    context = {"blocks": blocks, "chosen_block": block_id, "hybrid_blocks": block}

    if block is not None:
        start_date = get_start_date(request)
        scheduled_activities = None
        for b in block:
            if scheduled_activities is not None:
                scheduled_activities = scheduled_activities | b.eighthscheduledactivity_set.filter(
                    block__date__gte=start_date, attendance_taken=False
                ).order_by(
                    "-activity__special", "activity__name"
                )  # float special to top
            else:
                scheduled_activities = b.eighthscheduledactivity_set.filter(block__date__gte=start_date, attendance_taken=False).order_by(
                    "-activity__special", "activity__name"
                )  # float special to top

        context["scheduled_activities"] = scheduled_activities

        if request.POST.get("take_attendance_zero", False) is not False:
            zero_students = scheduled_activities.filter(members=None)
            signups = EighthSignup.objects.filter(scheduled_activity__in=zero_students)
            logger.debug(zero_students)
            if signups.count() == 0:
                zero_students.update(attendance_taken=True)
                messages.success(request, "Took attendance for {} empty activities.".format(zero_students.count()))
            else:
                messages.error(request, "Apparently there were actually {} signups. Maybe one is no longer empty?".format(signups.count()))
            return redirect("/eighth/admin/hybrid/no_attendance?block={},{}".format(block_id[0], block_id[1]))

        if request.POST.get("take_attendance_cancelled", False) is not False:
            cancelled = scheduled_activities.filter(cancelled=True)
            signups = EighthSignup.objects.filter(scheduled_activity__in=cancelled)
            logger.debug(cancelled)
            logger.debug(signups)
            signups.update(was_absent=True)
            cancelled.update(attendance_taken=True)
            messages.success(
                request, "Took attendance for {} cancelled activities. {} students marked absent.".format(cancelled.count(), signups.count())
            )
            return redirect("/eighth/admin/hybrid/no_attendance?block={},{}".format(block_id[0], block_id[1]))

    context["admin_page_title"] = "Hybrid Activities That Haven't Taken Attendance"
    return render(request, "eighth/admin/activities_without_attendance_hybrid.html", context)


@eighth_admin_required
def list_sponsor_view(request):
    block_id = request.GET.get("block", None)
    block = None

    blocks_set = set()
    for b in EighthBlock.objects.filter(
        eighthscheduledactivity__in=EighthScheduledActivity.objects.filter(activity__name="z - Hybrid Sticky").filter(
            block__date__gte=get_start_date(request)
        )
    ):
        blocks_set.add((str(b.date), b.block_letter[0]))
    blocks = sorted(list(blocks_set))

    if block_id is not None:
        try:
            block_id = tuple(block_id.split(","))
            block = EighthBlock.objects.filter(date=block_id[0], block_letter__contains=block_id[1])
        except (EighthBlock.DoesNotExist, ValueError):
            pass

    context = {"blocks": blocks, "chosen_block": block_id, "hybrid_blocks": block}

    if block is not None:
        acts = EighthScheduledActivity.objects.filter(block__in=block)
        lst = {}
        for sponsor in EighthSponsor.objects.all():
            lst[sponsor] = []
        for act in acts.prefetch_related("sponsors").prefetch_related("rooms"):
            for sponsor in act.get_true_sponsors():
                lst[sponsor].append(act)
        lst = sorted(lst.items(), key=lambda x: x[0].name)
        context["sponsor_list"] = lst

    context["admin_page_title"] = "Hybrid Sponsor Schedule List"
    return render(request, "eighth/admin/list_sponsors_hybrid.html", context)
