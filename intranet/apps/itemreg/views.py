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

    calculators = CalculatorRegistration.objects.filter(user=request.user)
    phones = PhoneRegistration.objects.filter(user=request.user)
    computers = ComputerRegistration.objects.filter(user=request.user)
    context = {
        "registered_devices": (calculators or phones or computers),
        "calculators": calculators,
        "computers": computers,
        "phones": phones,
        "lost": lost,
        "found": found,
        "previous_page": lost.previous_page_number if lost.previous_page_number else found.previous_page_number,
        "next_page": lost.next_page_number if lost.next_page_number else found.next_page_number 
    }
    return render(request, "itemreg/home.html", context)

@login_required
def register_calculator_view(request):
    """Register a calculator."""
    if request.method == "POST":
        form = CalculatorRegistrationForm(request.POST)
        logger.debug(form)
        if form.is_valid():
            obj = form.save()
            obj.user = request.user
            obj.save()
            messages.success(request, "Successfully added calculator.")
            return redirect("itemreg")
        else:
            messages.error(request, "Error adding calculator.")
    else:
        form = CalculatorRegistrationForm()
    return render(request, "itemreg/register_form.html", {"form": form, "action": "add", "type": "calculator", "form_route": "itemreg_calculator"})

@login_required
def register_computer_view(request):
    """Register a computer."""
    if request.method == "POST":
        form = ComputerRegistrationForm(request.POST)
        logger.debug(form)
        if form.is_valid():
            obj = form.save()
            obj.user = request.user
            obj.save()
            messages.success(request, "Successfully added computer.")
            return redirect("itemreg")
        else:
            messages.error(request, "Error adding computer.")
    else:
        form = ComputerRegistrationForm()
    return render(request, "itemreg/register_form.html", {"form": form, "action": "add", "type": "computer", "form_route": "itemreg_computer"})

@login_required
def register_phone_view(request):
    """Register a phone."""
    if request.method == "POST":
        form = PhoneRegistrationForm(request.POST)
        logger.debug(form)
        if form.is_valid():
            obj = form.save()
            obj.user = request.user
            obj.save()
            messages.success(request, "Successfully added phone.")
            return redirect("itemreg")
        else:
            messages.error(request, "Error adding phone.")
    else:
        form = PhoneRegistrationForm()
    return render(request, "itemreg/register_form.html", {"form": form, "action": "add", "type": "phone", "form_route": "itemreg_phone"})

@login_required
def register_delete_view(request, type, id):
    if type == "calculator":
        obj = CalculatorRegistration.objects.get(id=id)
    elif type == "computer":
        obj = ComputerRegistration.objects.get(id=id)
    elif type == "phone":
        obj = PhoneRegistration.objects.get(id=id)
    else:
        raise http.Http404

    if request.method == "POST" and "confirm" in request.POST:
        if obj.user == request.user:
            obj.delete()
            messages.success(request, "Deleted {}".format(type))
            return redirect("itemreg")

    return render(request, "itemreg/register_delete.html", {"type": type, "id": id, "obj": obj})


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


@login_required
def lostitem_view(request, item_id):
    """View a lostitem.

    id: lostitem id

    """
    lostitem = get_object_or_404(LostItem, id=item_id)
    return render(request, "itemreg/item_view.html", {"item": lostitem, "type": "lost"})


@login_required
def founditem_add_view(request):
    """Add a founditem."""
    if request.method == "POST":
        form = FoundItemForm(request.POST)
        logger.debug(form)
        if form.is_valid():
            obj = form.save()
            obj.user = request.user
            # SAFE HTML
            obj.description = bleach.linkify(obj.description)
            obj.save()
            messages.success(request, "Successfully added found item.")
            return redirect("founditem_view", obj.id)
        else:
            messages.error(request, "Error adding found item.")
    else:
        form = FoundItemForm()
    return render(request, "itemreg/founditem_form.html", {"form": form, "action": "add"})


@login_required
def founditem_modify_view(request, item_id=None):
    """Modify a founditem.

    id: founditem id

    """
    if request.method == "POST":
        founditem = get_object_or_404(FoundItem, id=item_id)
        form = FoundItemForm(request.POST, instance=founditem)
        if form.is_valid():
            obj = form.save()
            logger.debug(form.cleaned_data)
            # SAFE HTML
            obj.description = bleach.linkify(obj.description)
            obj.save()
            messages.success(request, "Successfully modified found item.")
            return redirect("founditem_view", obj.id)
        else:
            messages.error(request, "Error adding found item.")
    else:
        founditem = get_object_or_404(FoundItem, id=item_id)
        form = FoundItemForm(instance=founditem)

    context = {"form": form, "action": "modify", "id": item_id, "founditem": founditem}
    return render(request, "itemreg/founditem_form.html", context)


@login_required
def founditem_delete_view(request, item_id):
    """Delete a founditem.

    id: founditem id

    """
    if request.method == "POST":
        try:
            a = FoundItem.objects.get(id=item_id)
            if request.POST.get("full_delete", False):
                a.delete()
                messages.success(request, "Successfully deleted found item.")
            else:
                a.found = True
                a.save()
                messages.success(request, "Successfully marked found item as found!")
        except Announcement.DoesNotExist:
            pass

        return redirect("index")
    else:
        founditem = get_object_or_404(FoundItem, id=item_id)
        return render(request, "itemreg/founditem_delete.html", {"founditem": founditem})


@login_required
def founditem_view(request, item_id):
    """View a founditem.

    id: founditem id

    """
    founditem = get_object_or_404(FoundItem, id=item_id)
    return render(request, "itemreg/item_view.html", {"item": founditem, "type": "found"})
