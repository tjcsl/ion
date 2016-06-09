# -*- coding: utf-8 -*-

import logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import ParkingApplication, CarApplication
from .forms import ParkingApplicationForm, CarApplicationForm
from ..users.models import User

logger = logging.getLogger(__name__)


@login_required
def parking_intro_view(request):
    if not request.user.can_request_parking:
        messages.error(request, "You can't request a parking space.")
        return redirect("/")
    context = {"user": request.user}
    return render(request, "parking/intro.html", context)


@login_required
def parking_form_view(request):
    if not request.user.can_request_parking:
        messages.error(request, "You can't request a parking space.")
        return redirect("index")
    user = request.user
    if request.user.has_admin_permission('parking'):
        if "user" in request.GET:
            user = get_object_or_404(User, id=request.GET["user"])
        elif "user" in request.POST:
            user = get_object_or_404(User, id=request.POST["user"])
    try:
        app = ParkingApplication.objects.get(user=user)
    except ParkingApplication.DoesNotExist:
        app = None

    try:
        in_joint = ParkingApplication.objects.get(joint_user=request.user)
    except ParkingApplication.DoesNotExist:
        in_joint = False

    if request.method == "POST":
        if app:
            form = ParkingApplicationForm(request.POST, instance=app)
        else:
            form = ParkingApplicationForm(request.POST)
        logger.debug(form)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            if app:
                messages.success(request, "Successfully updated.")
            else:
                messages.success(request, "Successfully added. Now add at least one car.")
            return redirect("parking_form")
        else:
            messages.error(request, "Error adding.")
    else:
        if app:
            form = ParkingApplicationForm(instance=app)
        else:
            form = ParkingApplicationForm()
    return render(request, "parking/form.html", {"form": form, "app": app, "in_joint": in_joint})


@login_required
def parking_car_view(request):
    if not request.user.can_request_parking:
        messages.error(request, "You can't request a parking space.")
        return redirect("index")
    try:
        car = CarApplication.objects.get(id=request.GET.get("id", None))
    except CarApplication.DoesNotExist:
        car = None
    else:
        if not request.user.has_admin_permission('parking') and car.user != request.user:
            messages.error(request, "This isn't your car!")
            return redirect("parking")

    if "delete" in request.POST and car:
        car.delete()
        messages.success(request, "Deleted car")
        return redirect("parking_form")

    try:
        app = ParkingApplication.objects.get(user=request.user)
    except ParkingApplication.DoesNotExist:
        messages.error(request, "Please fill in the first stage of the form by clicking 'Submit' first.")
        return redirect("parking_form")

    if request.method == "POST":
        if car:
            form = CarApplicationForm(request.POST, instance=car)
        else:
            form = CarApplicationForm(request.POST)

        logger.debug(form)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            app.cars.add(obj)
            app.save()
            messages.success(request, "Successfully added.")
            return redirect("parking_form")
        else:
            messages.error(request, "Error adding.")
    else:
        if car:
            form = CarApplicationForm(instance=car)
        else:
            form = CarApplicationForm()
    return render(request, "parking/car.html", {"form": form, "car": car, "app": app})


@login_required
def parking_joint_view(request):
    if not request.user.can_request_parking:
        messages.error(request, "You can't request a parking space.")
        return redirect("index")

    user = request.user
    if request.user.has_admin_permission('parking'):
        if "user" in request.GET:
            user = get_object_or_404(User, id=request.GET["user"])
        elif "user" in request.POST:
            user = get_object_or_404(User, id=request.POST["user"])
    try:
        app = ParkingApplication.objects.get(user=user)
    except ParkingApplication.DoesNotExist:
        app = None
        messages.error(request, "Please fill in the first stage of the form by clicking 'Submit' first.")
        return redirect("parking_form")

    try:
        in_joint = ParkingApplication.objects.get(joint_user=request.user)
    except ParkingApplication.DoesNotExist:
        in_joint = False

    if in_joint and "disagree" in request.GET:
        in_joint.joint_user = None
        in_joint.save()
        messages.success(request, "Removed the joint application created with your name.")
        return redirect("parking_form")

    if "delete" in request.POST and app:
        app.joint_user = None
        app.save()
        messages.success(request, "Removed joint application.")
    elif "joint" in request.POST:
        try:
            app.joint_user = User.objects.get(username=request.POST["joint"])
        except User.DoesNotExist:
            messages.error(request, "Invalid user. Try again")
        else:
            app.save()
            messages.success(request, "Added a joint user.")

    return render(request, "parking/joint.html", {"user": user, "app": app})
