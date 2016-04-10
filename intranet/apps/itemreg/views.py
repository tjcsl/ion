# -*- coding: utf-8 -*-

import bleach
import logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect, get_object_or_404
from .models import LostItem, FoundItem
from .forms import LostItemForm

logger = logging.getLogger(__name__)


@login_required
def home_view(request):
    lost_all = LostItem.objects.all()
    lost_pg = Paginator(lost_all, 20)

    found_all = FoundItem.objects.all()
    found_pg = Paginator(found_all, 20)

    page = request.GET.get("page", 1)
    try:
        lost = lost_pg.page(page)
        found = found_pg.page(page)
    except (PageNotAnInteger, EmptyPage):
        lost = lost_pg.page(1)
        found = found_pg.page(1)

    context = {
        "lost": lost,
        "found": found
    }
    return render(request, "itemreg/home.html", context)


@login_required
def lostitem_add_view(request):
    """Add a lostitem."""
    if request.method == "POST":
        form = LostItemForm(request.POST)
        logger.debug(form)
        if form.is_valid():
            obj = form.save()
            obj.user = request.user
            # SAFE HTML
            obj.description = bleach.linkify(obj.description)
            obj.save()
            messages.success(request, "Successfully added lost item.")
            return redirect("lostitem_view", obj.id)
        else:
            messages.error(request, "Error adding lost item.")
    else:
        form = LostItemForm()
    return render(request, "itemreg/lostitem_form.html", {"form": form, "action": "add"})


@login_required
def lostitem_modify_view(request, item_id=None):
    """Modify a lostitem.

    id: lostitem id

    """
    if request.method == "POST":
        lostitem = get_object_or_404(LostItem, id=item_id)
        form = LostItemForm(request.POST, instance=lostitem)
        if form.is_valid():
            obj = form.save()
            logger.debug(form.cleaned_data)
            # SAFE HTML
            obj.description = bleach.linkify(obj.description)
            obj.save()
            messages.success(request, "Successfully modified lost item.")
            return redirect("lostitem_view", obj.id)
        else:
            messages.error(request, "Error adding lost item.")
    else:
        lostitem = get_object_or_404(LostItem, id=item_id)
        form = LostItemForm(instance=lostitem)

    context = {"form": form, "action": "modify", "id": item_id, "lostitem": lostitem}
    return render(request, "itemreg/lostitem_form.html", context)


@login_required
def lostitem_delete_view(request, item_id):
    """Delete a lostitem.

    id: lostitem id

    """
    if request.method == "POST":
        try:
            a = LostItem.objects.get(id=item_id)
            if request.POST.get("full_delete", False):
                a.delete()
                messages.success(request, "Successfully deleted lost item.")
            else:
                a.found = True
                a.save()
                messages.success(request, "Successfully marked lost item as found!")
        except LostItem.DoesNotExist:
            pass

        return redirect("index")
    else:
        lostitem = get_object_or_404(LostItem, id=item_id)
        return render(request, "itemreg/lostitem_delete.html", {"lostitem": lostitem})


def founditem_add_view(request):
    pass


def founditem_delete_view(request):
    pass
