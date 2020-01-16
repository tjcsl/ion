import logging

from django import http
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from intranet import settings

from ...utils.html import safe_html
from ..auth.decorators import announcements_admin_required, deny_restricted
from ..dashboard.views import dashboard_view
from ..groups.models import Group
from .forms import AnnouncementForm, AnnouncementRequestForm
from .models import Announcement, AnnouncementRequest
from .notifications import (admin_request_announcement_email, announcement_approved_email, announcement_posted_email, announcement_posted_twitter,
                            request_announcement_email)

logger = logging.getLogger(__name__)


@login_required
@deny_restricted
def view_announcements(request):
    """Show the dashboard with only announcements."""
    return dashboard_view(request, show_widgets=False, ignore_dashboard_types=["event"])


@login_required
@deny_restricted
def view_announcements_archive(request):
    """Show the dashboard with only announcements, showing expired posts."""
    return dashboard_view(request, show_widgets=False, show_expired=True, ignore_dashboard_types=["event"])


def announcement_posted_hook(request, obj):
    """Runs whenever a new announcement is created, or a request is approved and posted.

    obj: The Announcement object

    """
    if obj.notify_post:
        announcement_posted_twitter(request, obj)
        try:
            notify_all = obj.notify_email_all
        except AttributeError:
            notify_all = False

        try:
            if notify_all:
                announcement_posted_email(request, obj, True)
            else:
                announcement_posted_email(request, obj)
        except Exception as e:
            logger.error("Exception when emailing announcement: %s", e)
            messages.error(request, "Exception when emailing announcement: {}".format(e))
            raise e
    else:
        logger.debug("Announcement notify off")


def announcement_approved_hook(request, obj, req):
    """Runs whenever an administrator approves an announcement request.

    obj: the Announcement object
    req: the AnnouncementRequest object

    """
    announcement_approved_email(request, obj, req)


@login_required
def request_announcement_view(request):
    """The request announcement page."""
    if request.method == "POST":
        form = AnnouncementRequestForm(request.POST)

        if form.is_valid():
            teacher_objs = form.cleaned_data["teachers_requested"]

            if len(teacher_objs) > 2:
                messages.error(request, "Please select a maximum of 2 teachers to approve this post.")
            else:
                obj = form.save(commit=True)
                obj.user = request.user
                # SAFE HTML
                obj.content = safe_html(obj.content)

                obj.save()

                ann = AnnouncementRequest.objects.get(id=obj.id)
                approve_self = False
                for teacher in teacher_objs:
                    ann.teachers_requested.add(teacher)
                    if teacher == request.user:
                        ann.teachers_approved.add(teacher)
                        approve_self = True
                ann.save()

                if approve_self:
                    if settings.SEND_ANNOUNCEMENT_APPROVAL:
                        admin_request_announcement_email(request, form, ann)
                    ann.admin_email_sent = True
                    ann.save()
                    return redirect("request_announcement_success_self")

                else:
                    if settings.SEND_ANNOUNCEMENT_APPROVAL:
                        request_announcement_email(request, form, obj)
                    return redirect("request_announcement_success")
                return redirect("index")
        else:
            messages.error(request, "Error adding announcement request")
    else:
        form = AnnouncementRequestForm()
    return render(request, "announcements/request.html", {"form": form, "action": "add"})


@login_required
def request_announcement_success_view(request):
    return render(request, "announcements/success.html", {"type": "request"})


@login_required
def request_announcement_success_self_view(request):
    return render(request, "announcements/success.html", {"type": "request", "self": True})


@login_required
@deny_restricted
def approve_announcement_view(request, req_id):
    """The approve announcement page. Teachers will be linked to this page from an email.

    req_id: The ID of the AnnouncementRequest

    """
    req = get_object_or_404(AnnouncementRequest, id=req_id)

    requested_teachers = req.teachers_requested.all()
    if request.user not in requested_teachers:
        messages.error(request, "You do not have permission to approve this announcement.")
        return redirect("index")

    if request.method == "POST":
        form = AnnouncementRequestForm(request.POST, instance=req)
        if form.is_valid():
            obj = form.save(commit=True)
            # SAFE HTML
            obj.content = safe_html(obj.content)
            obj.save()
            if "approve" in request.POST:
                obj.teachers_approved.add(request.user)
                obj.save()
                if not obj.admin_email_sent:
                    if settings.SEND_ANNOUNCEMENT_APPROVAL:
                        admin_request_announcement_email(request, form, obj)
                    obj.admin_email_sent = True
                    obj.save()

                return redirect("approve_announcement_success")
            else:
                obj.save()
                return redirect("approve_announcement_reject")

    form = AnnouncementRequestForm(instance=req)
    context = {"form": form, "req": req, "admin_approve": False}
    return render(request, "announcements/approve.html", context)


@login_required
@deny_restricted
def approve_announcement_success_view(request):
    return render(request, "announcements/success.html", {"type": "approve", "status": "accept"})


@login_required
@deny_restricted
def approve_announcement_reject_view(request):
    return render(request, "announcements/success.html", {"type": "approve", "status": "reject"})


@announcements_admin_required
@deny_restricted
def admin_approve_announcement_view(request, req_id):
    """The administrator approval announcement request page. Admins will view this page through the
    UI.

    req_id: The ID of the AnnouncementRequest

    """
    req = get_object_or_404(AnnouncementRequest, id=req_id)

    if request.method == "POST":
        form = AnnouncementRequestForm(request.POST, instance=req)
        if form.is_valid():
            req = form.save(commit=True)
            # SAFE HTML
            req.content = safe_html(req.content)
            if "approve" in request.POST:
                groups = []
                if "groups" in request.POST:
                    group_ids = request.POST.getlist("groups")
                    groups = Group.objects.filter(id__in=group_ids)
                announcement = Announcement.objects.create(
                    title=req.title, content=req.content, author=req.author, user=req.user, expiration_date=req.expiration_date
                )
                for g in groups:
                    announcement.groups.add(g)
                announcement.save()

                req.posted = announcement
                req.posted_by = request.user
                req.save()

                announcement_approved_hook(request, announcement, req)
                announcement_posted_hook(request, announcement)

                messages.success(request, "Successfully approved announcement request. It has been posted.")
            else:
                req.rejected = True
                req.rejected_by = request.user
                req.save()
                messages.success(request, "You did not approve this request. It will be hidden.")
            return redirect("index")

    form = AnnouncementRequestForm(instance=req)
    all_groups = Group.objects.all()
    context = {"form": form, "req": req, "admin_approve": True, "all_groups": all_groups}
    return render(request, "announcements/approve.html", context)


@announcements_admin_required
@deny_restricted
def admin_request_status_view(request):
    all_waiting = AnnouncementRequest.objects.filter(posted=None, rejected=False).this_year()
    awaiting_teacher = all_waiting.filter(teachers_approved__isnull=True)
    awaiting_approval = all_waiting.filter(teachers_approved__isnull=False)
    approved = AnnouncementRequest.objects.exclude(posted=None).this_year()
    rejected = AnnouncementRequest.objects.filter(rejected=True).this_year()

    context = {"awaiting_teacher": awaiting_teacher, "awaiting_approval": awaiting_approval, "approved": approved, "rejected": rejected}

    return render(request, "announcements/request_status.html", context)


@announcements_admin_required
@deny_restricted
def add_announcement_view(request):
    """Add an announcement."""
    if request.method == "POST":
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            obj = form.save()
            obj.user = request.user
            # SAFE HTML
            obj.content = safe_html(obj.content)
            obj.save()
            announcement_posted_hook(request, obj)
            messages.success(request, "Successfully added announcement.")
            return redirect("index")
        else:
            messages.error(request, "Error adding announcement")
    else:
        form = AnnouncementForm()
    return render(request, "announcements/add_modify.html", {"form": form, "action": "add"})


@login_required
@deny_restricted
def view_announcement_view(request, announcement_id):
    """View an announcement.

    announcement_id: announcement id

    """
    announcement = get_object_or_404(Announcement, id=announcement_id)

    return render(request, "announcements/view.html", {"announcement": announcement})


@announcements_admin_required
@deny_restricted
def modify_announcement_view(request, announcement_id=None):
    """Modify an announcement.

    announcement_id: announcement id

    """
    if request.method == "POST":
        announcement = get_object_or_404(Announcement, id=announcement_id)
        form = AnnouncementForm(request.POST, instance=announcement)
        if form.is_valid():
            obj = form.save()
            if "update_added_date" in form.cleaned_data and form.cleaned_data["update_added_date"]:
                obj.added = timezone.now()
            # SAFE HTML
            obj.content = safe_html(obj.content)
            obj.save()
            messages.success(request, "Successfully modified announcement.")
            return redirect("index")
        else:
            messages.error(request, "Error adding announcement")
    else:
        announcement = get_object_or_404(Announcement, id=announcement_id)
        form = AnnouncementForm(instance=announcement)

    context = {"form": form, "action": "modify", "id": announcement_id, "announcement": announcement}
    return render(request, "announcements/add_modify.html", context)


@announcements_admin_required
@deny_restricted
def delete_announcement_view(request, announcement_id):
    """Delete an announcement.

    announcement_id: announcement id

    """
    if request.method == "POST":
        post_id = None
        try:
            post_id = request.POST["id"]
        except AttributeError:
            post_id = None
        try:
            a = Announcement.objects.get(id=post_id)
            if request.POST.get("full_delete", False):
                a.delete()
                messages.success(request, "Successfully deleted announcement.")
            else:
                a.expiration_date = timezone.localtime()
                a.save()
                messages.success(request, "Successfully expired announcement.")
        except Announcement.DoesNotExist:
            pass

        return redirect("index")
    else:
        announcement = get_object_or_404(Announcement, id=announcement_id)
        return render(request, "announcements/delete.html", {"announcement": announcement})


@login_required
@deny_restricted
@transaction.atomic
def show_announcement_view(request):
    """ Unhide an announcement that was hidden by the logged-in user.

        announcements_hidden in the user model is the related_name for
        "users_hidden" in the announcement model.
    """
    if request.method == "POST":
        announcement_id = request.POST.get("announcement_id")
        if announcement_id:
            announcement = Announcement.objects.get(id=announcement_id)
            announcement.user_map.users_hidden.remove(request.user)
            announcement.user_map.save()
            return http.HttpResponse("Unhidden")
        raise http.Http404
    else:
        return http.HttpResponseNotAllowed(["POST"], "HTTP 405: METHOD NOT ALLOWED")


@login_required
@deny_restricted
@transaction.atomic
def hide_announcement_view(request):
    """ Hide an announcement for the logged-in user.

        announcements_hidden in the user model is the related_name for
        "users_hidden" in the announcement model.
    """
    if request.method == "POST":
        announcement_id = request.POST.get("announcement_id")
        if announcement_id:
            announcement = Announcement.objects.get(id=announcement_id)
            try:
                announcement.user_map.users_hidden.add(request.user)
                announcement.user_map.save()
            except IntegrityError:
                logger.warning("Duplicate value when hiding announcement %d for %s.", announcement_id, request.user.username)
            return http.HttpResponse("Hidden")
        raise http.Http404
    else:
        return http.HttpResponseNotAllowed(["POST"], "HTTP 405: METHOD NOT ALLOWED")
