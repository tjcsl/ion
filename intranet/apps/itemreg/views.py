# -*- coding: utf-8 -*-

import logging
from django import http
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect, get_object_or_404
from .models import LostItem, FoundItem, CalculatorRegistration, ComputerRegistration, PhoneRegistration
from .forms import LostItemForm, FoundItemForm, CalculatorRegistrationForm, ComputerRegistrationForm, PhoneRegistrationForm

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

def lostitem_add_view(request):
    pass

def lostitem_delete_view(request):
    pass

def founditem_add_view(request):
    pass

def founditem_delete_view(request):
    pass
