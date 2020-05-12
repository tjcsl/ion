import logging
import pickle
import re

from cacheops import invalidate_model

from django import http
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from ....auth.decorators import eighth_admin_required
from ...forms.admin.blocks import BlockForm, QuickBlockForm
from ...models import EighthBlock, EighthScheduledActivity, EighthSignup
from ..attendance import generate_roster_pdf

logger = logging.getLogger(__name__)


@eighth_admin_required
def add_block_view(request):
    if request.method == "POST" and "custom_block" in request.POST:
        form = QuickBlockForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully added block.")
            return redirect("eighth_admin_dashboard")
        else:
            messages.error(request, "Error adding block.")
            request.session["add_block_form"] = pickle.dumps(form)

    date = None
    show_letters = None

    if "date" in request.GET:
        date = request.GET.get("date")
    if "date" in request.POST:
        date = request.POST.get("date")
    title_suffix = ""
    if date:
        date_format = re.compile(r"([0-9]{2})\/([0-9]{2})\/([0-9]{4})")
        fmtdate = date_format.sub(r"\3-\1-\2", date)
        title_suffix = " - {}".format(fmtdate)
        show_letters = True

        if "modify_blocks" in request.POST:
            letters = request.POST.getlist("blocks")
            current_letters = []
            blocks_day = EighthBlock.objects.filter(date=fmtdate)
            for day in blocks_day:
                current_letters.append(day.block_letter)
            for ltr in letters:
                if not ltr:
                    continue
                if ltr not in current_letters:
                    EighthBlock.objects.create(date=fmtdate, block_letter=ltr)
                    messages.success(request, "Successfully added {} Block on {}".format(ltr, fmtdate))
            for ltr in current_letters:
                if not ltr:
                    continue
                if ltr not in letters:
                    EighthBlock.objects.get(date=fmtdate, block_letter=ltr).delete()
                    messages.success(request, "Successfully removed {} Block on {}".format(ltr, fmtdate))

            invalidate_model(EighthBlock)

    letters = []
    visible_blocks = ["A", "B", "C", "D", "E", "F", "G", "H"]
    if show_letters:
        onday = EighthBlock.objects.filter(date=fmtdate)
        for ltr in visible_blocks:
            exists = onday.filter(block_letter=ltr)
            letters.append({"name": ltr, "exists": exists})
        for blk in onday:
            if blk.block_letter not in visible_blocks:
                visible_blocks.append(blk.block_letter)
                letters.append({"name": blk.block_letter, "exists": True})

    context = {
        "admin_page_title": "Add or Remove Blocks{}".format(title_suffix),
        "date": date,
        "letters": letters,
        "show_letters": show_letters,
        "add_block_form": QuickBlockForm,
    }

    return render(request, "eighth/admin/add_block.html", context)


@eighth_admin_required
def edit_block_view(request, block_id):
    try:
        block = EighthBlock.objects.get(id=block_id)
    except EighthBlock.DoesNotExist:
        raise http.Http404

    if request.method == "POST":
        form = BlockForm(request.POST, instance=block)
        if form.is_valid():
            form.save()
            invalidate_model(EighthBlock)
            messages.success(request, "Successfully edited block.")
            return redirect("eighth_admin_dashboard")
        else:
            messages.error(request, "Error adding block.")
    else:
        form = BlockForm(instance=block)

    context = {
        "form": form,
        "delete_url": reverse("eighth_admin_delete_block", args=[block_id]),
        "admin_page_title": "Edit Block",
        "block_id": block_id,
    }
    return render(request, "eighth/admin/edit_form.html", context)


@eighth_admin_required
def copy_block_view(request, block_id):
    try:
        block = EighthBlock.objects.get(id=block_id)
    except EighthBlock.DoesNotExist:
        raise http.Http404

    if request.method == "POST":
        copy_signups = request.POST.get("signups", False)
        new_block_id = request.POST.get("block", None)
        if new_block_id and not new_block_id == block_id:
            new_block = None
            try:
                new_block = EighthBlock.objects.get(id=new_block_id)
            except EighthBlock.DoesNotExist:
                messages.error(request, "That block does not exist!")
            if new_block:
                # Delete previous EighthScheduledActivities and EighthSignups
                EighthScheduledActivity.objects.filter(block=block).delete()
                EighthSignup.objects.filter(scheduled_activity__block=block).delete()

                for schact in EighthScheduledActivity.objects.filter(block=new_block, cancelled=False).prefetch_related("rooms", "sponsors"):
                    new_schact = EighthScheduledActivity.objects.create(
                        block=block, activity=schact.activity, both_blocks=schact.both_blocks, special=schact.special
                    )
                    new_schact.sponsors.set(schact.sponsors.all())
                    new_schact.rooms.set(schact.rooms.all())
                    new_schact.save()
                    if copy_signups:
                        EighthSignup.objects.bulk_create(
                            [EighthSignup(user=s.user, scheduled_activity=new_schact) for s in EighthSignup.objects.filter(scheduled_activity=schact)]
                        )

                context = {
                    "new_activities": EighthScheduledActivity.objects.filter(block=block).count(),
                    "new_signups": EighthSignup.objects.filter(scheduled_activity__block=block).count(),
                    "success": True,
                    "admin_page_title": "Finished Copy Block - {} ({})".format(block.formatted_date, block.block_letter),
                    "block_id": block_id,
                }
                return render(request, "eighth/admin/copy_form.html", context)

        else:
            messages.error(request, "Please enter a valid block to copy activities from.")

    context = {
        "existing_activities": EighthScheduledActivity.objects.filter(block=block).count(),
        "existing_signups": EighthSignup.objects.filter(scheduled_activity__block=block).count(),
        "blocks": EighthBlock.objects.all().order_by("date"),
        "admin_page_title": "Copy Block - {} ({})".format(block.formatted_date, block.block_letter),
        "to_block": "{}: {} ({})".format(block.id, block.formatted_date, block.block_letter),
        "block_id": block_id,
        "locked": block.locked,
        "success": False,
    }
    return render(request, "eighth/admin/copy_form.html", context)


@eighth_admin_required
def delete_block_view(request, block_id):
    try:
        block = EighthBlock.objects.get(id=block_id)
    except EighthBlock.DoesNotExist:
        raise http.Http404

    if request.method == "POST":
        block.delete()
        invalidate_model(EighthBlock)
        messages.success(request, "Successfully deleted block.")
        return redirect("eighth_admin_dashboard")
    else:
        context = {
            "admin_page_title": "Delete Block",
            "item_name": str(block),
            "help_text": "Deleting this block will remove all records " "of it related to eighth period.",
        }

        return render(request, "eighth/admin/delete_form.html", context)


@eighth_admin_required
def print_block_rosters_view(request, block_id):
    if "schact_id" in request.POST:
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = 'inline; filename="block_{}_rosters.pdf"'.format(block_id)
        sched_act_ids = request.POST.getlist("schact_id")

        pdf_buffer = generate_roster_pdf(sched_act_ids)
        response.write(pdf_buffer.getvalue())
        pdf_buffer.close()
        return response
    else:
        try:
            block = EighthBlock.objects.get(id=block_id)
            schacts = EighthScheduledActivity.objects.filter(block=block).order_by("sponsors")
            schacts = sorted(schacts, key=lambda x: "{}".format(x.get_true_sponsors()))
        except (EighthBlock.DoesNotExist, EighthScheduledActivity.DoesNotExist):
            raise http.Http404
        context = {"eighthblock": block, "admin_page_title": "Choose activities to print", "schacts": schacts}
        return render(request, "eighth/admin/choose_roster_activities.html", context)
