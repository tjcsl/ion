import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from ..auth.decorators import deny_restricted
from .forms import CarApplicationForm, ParkingApplicationForm
from .models import CarApplication, ParkingApplication

logger = logging.getLogger(__name__)


@login_required
@deny_restricted
def parking_intro_view(request):
    if not settings.PARKING_ENABLED and not request.user.has_admin_permission("parking"):
        return redirect("index")

    if not request.user.can_request_parking:
        messages.error(request, "You can't request a parking space.")
        return redirect("index")

    context = {"user": request.user, "absences": request.user.absence_count(), "max_absences": settings.PARKING_MAX_ABSENCES}

    return render(request, "parking/intro.html", context)


@login_required
@deny_restricted
def parking_form_view(request):
    if not settings.PARKING_ENABLED and not request.user.has_admin_permission("parking"):
        return redirect("index")

    if not request.user.has_admin_permission("parking") and request.user.absence_count() > settings.PARKING_MAX_ABSENCES:
        return redirect("parking")

    if not request.user.can_request_parking:
        messages.error(request, "You can't request a parking space.")
        return redirect("index")
    user = request.user
    if request.user.has_admin_permission("parking"):
        if "user" in request.GET:
            user = get_object_or_404(get_user_model(), id=request.GET["user"])
        elif "user" in request.POST:
            user = get_object_or_404(get_user_model(), id=request.POST["user"])
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
@deny_restricted
def parking_car_view(request):
    if not settings.PARKING_ENABLED and not request.user.has_admin_permission("parking"):
        return redirect("index")

    if not request.user.has_admin_permission("parking") and request.user.absence_count() > settings.PARKING_MAX_ABSENCES:
        return redirect("parking")

    if not request.user.can_request_parking:
        messages.error(request, "You can't request a parking space.")
        return redirect("index")
    try:
        car = CarApplication.objects.get(id=request.GET.get("id", None))
    except CarApplication.DoesNotExist:
        car = None
    else:
        if not request.user.has_admin_permission("parking") and car.user != request.user:
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
@deny_restricted
def parking_joint_view(request):
    if not settings.PARKING_ENABLED and not request.user.has_admin_permission("parking"):
        return redirect("index")

    if not request.user.has_admin_permission("parking") and request.user.absence_count() > settings.PARKING_MAX_ABSENCES:
        return redirect("parking")

    if not request.user.can_request_parking:
        messages.error(request, "You can't request a parking space.")
        return redirect("index")

    user = request.user
    if request.user.has_admin_permission("parking"):
        if "user" in request.GET:
            user = get_object_or_404(get_user_model(), id=request.GET["user"])
        elif "user" in request.POST:
            user = get_object_or_404(get_user_model(), id=request.POST["user"])
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
            app.joint_user = get_user_model().objects.get(username=request.POST["joint"])
        except get_user_model().DoesNotExist:
            messages.error(request, "Invalid user. Try again")
        else:
            app.save()
            messages.success(request, "Added a joint user.")

    return render(request, "parking/joint.html", {"user": user, "app": app})
