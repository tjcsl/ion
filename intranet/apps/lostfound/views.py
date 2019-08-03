import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import get_object_or_404, redirect, render

from ...utils.html import safe_html
from ..auth.decorators import deny_restricted
from .forms import FoundItemForm, LostItemForm
from .models import FoundItem, LostItem

logger = logging.getLogger(__name__)


@login_required
@deny_restricted
def home_view(request):
    lost_all = LostItem.objects.all().order_by('id')
    lost_pg = Paginator(lost_all, 20)

    found_all = FoundItem.objects.all().order_by('id')
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
        "found": found,
        "previous_page": lost.previous_page_number if lost.previous_page_number else found.previous_page_number,
        "next_page": lost.next_page_number if lost.next_page_number else found.next_page_number,
        "is_lostfound_admin": request.user.has_admin_permission("lostfound")
    }
    return render(request, "lostfound/home.html", context)


@login_required
@deny_restricted
def lostitem_add_view(request):
    """Add a lostitem."""
    if request.method == "POST":
        form = LostItemForm(request.POST)
        logger.debug(form)
        if form.is_valid():
            obj = form.save()
            obj.user = request.user
            # SAFE HTML
            obj.description = safe_html(obj.description)
            obj.save()
            messages.success(request, "Successfully added lost item.")
            return redirect("lostitem_view", obj.id)
        else:
            messages.error(request, "Error adding lost item.")
    else:
        form = LostItemForm()
    return render(request, "lostfound/lostitem_form.html", {"form": form, "action": "add"})


@login_required
@deny_restricted
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
            obj.description = safe_html(obj.description)
            obj.save()
            messages.success(request, "Successfully modified lost item.")
            return redirect("lostitem_view", obj.id)
        else:
            messages.error(request, "Error adding lost item.")
    else:
        lostitem = get_object_or_404(LostItem, id=item_id)
        form = LostItemForm(instance=lostitem)

    context = {"form": form, "action": "modify", "id": item_id, "lostitem": lostitem}
    return render(request, "lostfound/lostitem_form.html", context)


@login_required
@deny_restricted
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
        return render(request, "lostfound/lostitem_delete.html", {"lostitem": lostitem})


@login_required
@deny_restricted
def lostitem_view(request, item_id):
    """View a lostitem.

    id: lostitem id

    """
    lostitem = get_object_or_404(LostItem, id=item_id)
    return render(request, "itemreg/item_view.html", {"item": lostitem, "type": "lost"})


@login_required
@deny_restricted
def founditem_add_view(request):
    """Add a founditem."""
    if request.method == "POST":
        form = FoundItemForm(request.POST)
        logger.debug(form)
        if form.is_valid():
            obj = form.save()
            obj.user = request.user
            # SAFE HTML
            obj.description = safe_html(obj.description)
            obj.save()
            messages.success(request, "Successfully added found item.")
            return redirect("founditem_view", obj.id)
        else:
            messages.error(request, "Error adding found item.")
    else:
        form = FoundItemForm()
    return render(request, "lostfound/founditem_form.html", {"form": form, "action": "add"})


@login_required
@deny_restricted
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
            obj.description = safe_html(obj.description)
            obj.save()
            messages.success(request, "Successfully modified found item.")
            return redirect("founditem_view", obj.id)
        else:
            messages.error(request, "Error adding found item.")
    else:
        founditem = get_object_or_404(FoundItem, id=item_id)
        form = FoundItemForm(instance=founditem)

    context = {"form": form, "action": "modify", "id": item_id, "founditem": founditem}
    return render(request, "lostfound/founditem_form.html", context)


@login_required
@deny_restricted
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
        except FoundItem.DoesNotExist:
            pass

        return redirect("index")
    else:
        founditem = get_object_or_404(FoundItem, id=item_id)
        return render(request, "lostfound/founditem_delete.html", {"founditem": founditem})


@login_required
@deny_restricted
def founditem_view(request, item_id):
    """View a founditem.

    id: founditem id

    """
    founditem = get_object_or_404(FoundItem, id=item_id)
    return render(request, "itemreg/item_view.html", {"item": founditem, "type": "found"})
