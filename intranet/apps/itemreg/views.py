# -*- coding: utf-8 -*-

import logging
from django import http
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import CalculatorRegistration, ComputerRegistration, PhoneRegistration
from .forms import CalculatorRegistrationForm, ComputerRegistrationForm, PhoneRegistrationForm
from ..search.views import get_search_results

logger = logging.getLogger(__name__)


@login_required
def home_view(request):
    calculators = CalculatorRegistration.objects.filter(user=request.user)
    phones = PhoneRegistration.objects.filter(user=request.user)
    computers = ComputerRegistration.objects.filter(user=request.user)
    context = {
        "registered_devices": (calculators or phones or computers),
        "calculators": calculators,
        "computers": computers,
        "phones": phones,
        "is_itemreg_admin": request.user.has_admin_permission("itemreg")
    }
    return render(request, "itemreg/home.html", context)


@login_required
def search_view(request):
    if not request.user.has_admin_permission("itemreg") and not request.user.is_teacher:
        return http.Http404

    type = request.GET.get("type", "")
    context = {
        "calc_form": CalculatorRegistrationForm(request.GET) if type == "calculator" else CalculatorRegistrationForm(),
        "comp_form": ComputerRegistrationForm(request.GET) if type == "computer" else ComputerRegistrationForm(),
        "phone_form": PhoneRegistrationForm(request.GET) if type == "phone" else PhoneRegistrationForm()
    }
    results = {"calculator": None, "computer": None, "phone": None}
    if type == "calculator":
        cresults = CalculatorRegistration.objects.all()
        logger.debug(cresults)

        calc_serial = request.GET.get("calc_serial")
        if calc_serial:
            cresults = cresults.filter(calc_serial__icontains=calc_serial)

        logger.debug(cresults)

        calc_id = request.GET.get("calc_id")
        if calc_id:
            cresults = cresults.filter(calc_id__icontains=calc_id)

        logger.debug(cresults)

        calc_type = request.GET.get("calc_type")
        if calc_type:
            cresults = cresults.filter(calc_type=calc_type)

        logger.debug(cresults)
        results["calculator"] = cresults
    elif type == "computer":
        cresults = ComputerRegistration.objects.all()
        logger.debug(cresults)

        manufacturer = request.GET.get("manufacturer")
        if manufacturer:
            cresults = cresults.filter(manufacturer=manufacturer)

        logger.debug(cresults)

        model = request.GET.get("model")
        if model:
            cresults = cresults.filter(model__icontains=model)

        logger.debug(cresults)

        serial = request.GET.get("serial")
        if serial:
            cresults = cresults.filter(serial__icontains=serial)

        logger.debug(cresults)

        screen_size = request.GET.get("screen_size")
        if screen_size:
            cresults = cresults.filter(screen_size=screen_size)

        logger.debug(cresults)
        results["computer"] = cresults
    elif type == "phone":
        cresults = PhoneRegistration.objects.all()
        logger.debug(cresults)

        manufacturer = request.GET.get("manufacturer")
        if manufacturer:
            cresults = cresults.filter(manufacturer=manufacturer)

        logger.debug(cresults)

        model = request.GET.get("model")
        if model:
            cresults = cresults.filter(model__icontains=model)

        logger.debug(cresults)

        serial = request.GET.get("serial")
        if serial:
            cresults = cresults.filter(serial__icontains=serial)

        logger.debug(cresults)
        results["phone"] = cresults
    elif type == "all":
        results["calculator"] = CalculatorRegistration.objects.all()
        results["computer"] = ComputerRegistration.objects.all()
        results["phone"] = PhoneRegistration.objects.all()

    quser = request.GET.get("user", None)
    if quser:
        try:
            _st, search = get_search_results(quser)
        except Exception:
            search = []

        logger.debug(search)

        for i in results:
            if results[i]:
                results[i] = results[i].filter(user__in=search)

    class NoneDict(dict):

        def __getitem__(self, key):
            return dict.get(self, key)

    getargs = NoneDict(dict(request.GET))

    context.update({
        "type": type,
        "results": results,
        "no_results": sum([len(results[i]) if results[i] else 0 for i in results]) < 1,
        "getargs": getargs
    })

    return render(request, "itemreg/search.html", context)


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
