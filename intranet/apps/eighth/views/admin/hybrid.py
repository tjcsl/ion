import logging
from typing import Optional

from formtools.wizard.views import SessionWizardView

from django import http
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render, reverse

from ....auth.decorators import eighth_admin_required
from ....users.models import Group
from ...forms.admin.activities import HybridActivitySelectionForm
from ...forms.admin.blocks import HybridBlockSelectionForm
from ...models import EighthBlock, EighthScheduledActivity, EighthSignup, EighthSponsor
from ...tasks import eighth_admin_signup_group_task_hybrid
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


@eighth_admin_required
def eighth_admin_groups_index_hybrid_view(request):
    groups = Group.objects.all()
    return render(
        request, "eighth/admin/hybrid_groups.html", context={"groups": groups, "url_id_placeholder": "734784857438457843756435654645642343465"}
    )


class EighthAdminSignUpGroupWizard(SessionWizardView):
    FORMS = [("block", HybridBlockSelectionForm), ("activity", HybridActivitySelectionForm)]

    TEMPLATES = {"block": "eighth/admin/sign_up_group.html", "activity": "eighth/admin/sign_up_group.html"}

    def get_template_names(self):
        return [self.TEMPLATES[self.steps.current]]

    def get_form_kwargs(self, step=None):
        kwargs = {}
        if step == "block":
            kwargs.update({"exclude_before_date": get_start_date(self.request)})
        if step == "activity":
            block = self.get_cleaned_data_for_step("block")["block"]
            kwargs.update({"block": block})

        labels = {"block": "Select a block", "activity": "Select an activity"}

        kwargs.update({"label": labels[step]})

        return kwargs

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)

        block = self.get_cleaned_data_for_step("block")
        if block:
            context.update({"block_obj": (block["block"][2:12], block["block"][16])})

        context.update({"admin_page_title": "Sign Up Group", "hybrid": True})
        return context

    def done(self, form_list, **kwargs):
        form_list = list(form_list)

        block = form_list[0].cleaned_data["block"]
        block_set = EighthBlock.objects.filter(date=block[2:12], block_letter__contains=block[16])
        virtual_block = block_set.filter(block_letter__contains="V")[0]
        person_block = block_set.filter(block_letter__contains="P")[0]

        activity = form_list[1].cleaned_data["activity"]
        scheduled_activity_virtual = EighthScheduledActivity.objects.get(block=virtual_block, activity=activity)
        scheduled_activity_person = EighthScheduledActivity.objects.get(block=person_block, activity=activity)

        try:
            group = Group.objects.get(id=kwargs["group_id"])
        except Group.DoesNotExist as e:
            raise http.Http404 from e

        return redirect(
            reverse("eighth_admin_signup_group_action_hybrid", args=[group.id, scheduled_activity_virtual.id, scheduled_activity_person.id])
        )


eighth_admin_signup_group_hybrid_view = eighth_admin_required(EighthAdminSignUpGroupWizard.as_view(EighthAdminSignUpGroupWizard.FORMS))


def eighth_admin_signup_group_action_hybrid(request, group_id, schact_virtual_id, schact_person_id):
    scheduled_activity_virtual = get_object_or_404(EighthScheduledActivity, id=schact_virtual_id)
    scheduled_activity_person = get_object_or_404(EighthScheduledActivity, id=schact_person_id)
    group = get_object_or_404(Group, id=group_id)

    users = group.user_set.all()

    if not users.exists():
        messages.info(request, "The group you have selected has no members.")
        return redirect("eighth_admin_dashboard")

    if "confirm" in request.POST:
        if request.POST.get("run_in_background"):
            eighth_admin_signup_group_task_hybrid.delay(
                user_id=request.user.id, group_id=group_id, schact_virtual_id=schact_virtual_id, schact_person_id=schact_person_id
            )
            messages.success(request, "Group members are being signed up in the background.")
            return redirect("eighth_admin_dashboard")
        else:
            eighth_admin_perform_group_signup(
                group_id=group_id, schact_virtual_id=schact_virtual_id, schact_person_id=schact_person_id, request=request
            )
            messages.success(request, "Successfully signed up group for activity.")
            return redirect("eighth_admin_dashboard")

    return render(
        request,
        "eighth/admin/sign_up_group.html",
        {
            "admin_page_title": "Confirm Group Signup",
            "hybrid": True,
            "scheduled_activity_virtual": scheduled_activity_virtual,
            "scheduled_activity_person": scheduled_activity_person,
            "group": group,
            "users_num": users.count(),
        },
    )


def eighth_admin_perform_group_signup(*, group_id: int, schact_virtual_id: int, schact_person_id: int, request: Optional[http.HttpRequest]):
    """Performs sign up of all users in a specific group up for a
    specific scheduled activity.

    Args:
        group_id: The ID of the group that should be signed up for the activity.
        schact_virtual_id: The ID of the EighthScheduledActivity all the virtual users in the group
            should be signed up for.
        schact_person_id: The ID of the EighthScheduledActivity all the in-person users in the group
            should be signed up for.
        request: If possible, the request object associated with the operation.

    """

    # We assume these exist
    scheduled_activity_virtual = EighthScheduledActivity.objects.get(id=schact_virtual_id)
    scheduled_activity_person = EighthScheduledActivity.objects.get(id=schact_person_id)
    group = Group.objects.get(id=group_id)

    is_P1_block = "P1" in scheduled_activity_person.block.block_letter

    virtual_group = Group.objects.get(name="virtual").user_set.all()
    person_group = Group.objects.get(name="in-person").user_set.all()

    if is_P1_block:
        virtual_group = virtual_group.union(Group.objects.get(name="in-person (l-z)").user_set.all())
        person_group = person_group.union(Group.objects.get(name="in-person (a-k)").user_set.all())
    else:
        virtual_group = virtual_group.union(Group.objects.get(name="in-person (a-k)").user_set.all())
        person_group = person_group.union(Group.objects.get(name="in-person (l-z)").user_set.all())

    for user in group.user_set.all():
        if user in virtual_group:
            scheduled_activity_virtual.add_user(user, request=request, force=True, no_after_deadline=True)
        elif user in person_group:
            scheduled_activity_person.add_user(user, request=request, force=True, no_after_deadline=True)
