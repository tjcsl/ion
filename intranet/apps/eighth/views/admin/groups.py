# -*- coding: utf-8 -*-

import csv
import logging
import pickle
import re

from cacheops import invalidate_model, invalidate_obj

from django import http
from django.contrib import messages
from django.core.cache import cache
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import redirect, render

from formtools.wizard.views import SessionWizardView

from ...forms.admin.activities import (
    ActivitySelectionForm, ScheduledActivityMultiSelectForm)
from ...forms.admin.blocks import BlockSelectionForm
from ...forms.admin.groups import GroupForm, QuickGroupForm, UploadGroupForm
from ...models import EighthActivity, EighthBlock, EighthScheduledActivity
from ...utils import get_start_date
from ....auth.decorators import eighth_admin_required
from ....groups.models import Group
from ....search.views import get_search_results
from ....users.models import User

logger = logging.getLogger(__name__)


@eighth_admin_required
def add_group_view(request):
    if request.method == "POST":
        form = QuickGroupForm(request.POST)
        if form.is_valid():
            group = form.save()
            messages.success(request, "Successfully added group.")
            return redirect("eighth_admin_edit_group", group_id=group.id)
        else:
            messages.error(request, "Error adding group.")
            try:
                request.session["add_group_form"] = pickle.dumps(form)
            except (pickle.PicklingError, TypeError):
                """Prevent pickle errors."""
                pass
            return redirect("eighth_admin_dashboard")
    else:
        return http.HttpResponseNotAllowed(["POST"], "405: METHOD NOT ALLOWED")


@eighth_admin_required
def edit_group_view(request, group_id):
    try:
        group = Group.objects.get(id=group_id)
    except Group.DoesNotExist:
        raise http.Http404

    if request.method == "POST":
        invalidate_model(Group)
        if group.name.lower().startswith("all students"):
            cache.delete("users:students")
        if "remove_all" in request.POST:
            users = group.user_set.all()
            num = users.count()
            for u in users:
                group.user_set.remove(u)
            group.save()
            invalidate_obj(group)
            messages.success(
                request, "Successfully deleted {} members of the group.".format(num))
            return redirect("eighth_admin_edit_group", group.id)
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            if 'student_visible' in form.cleaned_data:
                props = group.properties
                props.student_visible = form.cleaned_data['student_visible']
                props.save()
                invalidate_obj(props)

            form.save()
            messages.success(request, "Successfully edited group.")
            return redirect("eighth_admin_dashboard")
        else:
            messages.error(request, "Error modifying group.")
    else:
        form = GroupForm(
            instance=group, initial={"student_visible": group.properties.student_visible})

    student_query = None
    if request.method == "GET":
        student_query = request.GET.get("q", None)

    if not student_query:
        users = group.user_set.all()  # Order not strictly alphabetical
    else:
        ion_ids = [sid.strip() for sid in student_query.split(",")]
        users = group.user_set.filter(username__in=ion_ids)

    p = Paginator(users, 100)  # Paginating to limit LDAP queries (slow)

    page_num = request.GET.get('p', 1)
    try:
        page = p.page(page_num)
    except PageNotAnInteger:
        page = p.page(1)
    except EmptyPage:
        page = p.page(p.num_pages)
    members = []
    for user in page:
        grade = user.grade
        emails = user.emails
        members.append({
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "student_id": user.student_id,
            "email": user.tj_email if user.tj_email else emails[0] if emails else "",
            "grade": grade.number if user.grade and not user.grade.number == 13 else "Staff"
        })
    members = sorted(members, key=lambda m: (m["last_name"], m["first_name"]))
    linked_activities = EighthActivity.objects.filter(groups_allowed=group)

    def parse_int(value):
        return int(value) if value.isdigit() else None

    context = {
        "group": group,
        "members": members,
        "member_count": users.count(),
        "members_page": page,
        "edit_form": form,
        "added_ids": [parse_int(x) for x in request.GET.getlist("added")],
        "linked_activities": linked_activities,
        "admin_page_title": "Edit Group",
        "delete_url": reverse("eighth_admin_delete_group", args=[group_id])
    }

    if "possible_student" in request.GET:
        student_ids = request.GET.getlist("possible_student")
        possible_students = User.objects.get(id__in=student_ids)
        context["possible_students"] = possible_students

    return render(request, "eighth/admin/edit_group.html", context)


def get_file_string(fileobj):
    filetext = ""
    for chunk in fileobj.chunks():
        filetext += chunk.decode("ISO-8859-1")
    return filetext


def get_user_info(key, val):
    if key in ["username", "id"]:
        try:
            u = User.objects.filter(**{key: val})
        except ValueError:
            return []
        return u

    if key == "student_id":
        u = User.objects.user_with_student_id(val)
        return [u] if u else []

    if key == "name":
        if re.match("^[A-Za-z ]*$", val):
            vals = val.split(" ")
            if len(vals) == 2:
                u = User.objects.user_with_name(vals[0], vals[1])
                if u:
                    return [u]
            elif len(vals) == 3:
                u = User.objects.user_with_name(vals[0], vals[2])
                if u:
                    return [u]
            elif len(vals) == 1:
                # Try last name
                u = User.objects.user_with_name(None, vals[0])
                if u:
                    return [u]
                else:
                    # Try first name
                    u = User.objects.user_with_name(vals[0], None)
                    if u:
                        return [u]
        return []


def handle_group_input(filetext):
    logger.debug(filetext)
    lines = filetext.splitlines()

    return find_users_input(lines)


def find_users_input(lines):
    sure_users = []
    unsure_users = []
    for line in lines:
        done = False
        line = line.strip()

        if "," in line:
            parts = line.split(",")
            if len(parts) == 3:
                for part in parts:
                    if len(part) == 7:
                        # Try student ID
                        u = User.objects.user_with_student_id(part)
                        if u:
                            sure_users.append([line, u])
                            done = True
                            break
            else:
                line = " ".join(parts)

            if done:
                continue

        # Try username, user id
        for i in ["username", "id", "student_id", "name"]:
            r = get_user_info(i, line)
            if r:
                sure_users.append([line, r[0]])
                done = True
                break

        if not done and " " in line:
            # Reverse
            new_line = " ".join(line.split(" ")[::-1])
            r = get_user_info("name", new_line)
            if r:
                sure_users.append([line, r[0]])
                done = True

        if not done:
            unsure_users.append([line, r])

    logger.debug("Sure users:")
    logger.debug(sure_users)
    logger.debug("Unsure users:")
    logger.debug(unsure_users)

    return sure_users, unsure_users


@eighth_admin_required
def upload_group_members_view(request, group_id):
    try:
        group = Group.objects.get(id=group_id)
    except Group.DoesNotExist:
        raise http.Http404
    stage = "upload"
    data = {}
    filetext = False
    if request.method == "POST":
        form = UploadGroupForm(request)
        logger.debug(request.FILES)
        if "file" in request.FILES:
            fileobj = request.FILES['file']
            if "text/" not in fileobj.content_type:
                messages.error(
                    request, "The uploaded file is not of the correct type, plain text.")
                return redirect("eighth_admin_edit_group", group.id)
            filetext = get_file_string(fileobj)
        elif "filetext" in request.POST:
            filetext = request.POST.get("filetext")
        elif "user_id" in request.POST:
            userids = request.POST.getlist("user_id")
            num_added = 0
            for uid in userids:
                user = User.objects.get(id=uid)
                if user is None:
                    messages.error(
                        request, "User with ID {} does not exist".format(uid))
                else:
                    user.groups.add(group)
                    user.save()
                    num_added += 1
            invalidate_obj(group)
            messages.success(
                request, "{} added to group {}".format(num_added, group))
            return redirect("eighth_admin_edit_group", group.id)
        elif "import_group" in request.POST:
            try:
                import_group = Group.objects.get(
                    id=request.POST["import_group"])
            except Group.DoesNotExist:
                raise http.Http404
            num_users = import_group.user_set.count()
            if "import_confirm" in request.POST:
                for member in import_group.user_set.all():
                    member.groups.add(group)
                    member.save()
                invalidate_obj(group)
                messages.success(
                    request, "Added {} users from {} to {}".format(num_users, import_group, group))
                return redirect("eighth_admin_edit_group", group.id)
            return render(request, "eighth/admin/upload_group.html", {
                "admin_page_title": "Import Group Members: {}".format(group),
                "stage": "import_confirm",
                "group": group,
                "import_group": import_group,
                "num_users": num_users
            })

    else:
        form = UploadGroupForm()
    all_groups = Group.objects.order_by("name")
    context = {"admin_page_title": "Upload/Import Group Members: {}".format(group),
               "form": form,
               "stage": stage,
               "data": data,
               "group": group,
               "all_groups": all_groups}

    if filetext:
        context["stage"] = "parse"
        data = handle_group_input(filetext)
        context["sure_users"], context["unsure_users"] = data

    return render(request, "eighth/admin/upload_group.html", context)


@eighth_admin_required
def delete_group_view(request, group_id):
    try:
        group = Group.objects.get(id=group_id)
    except Group.DoesNotExist:
        raise http.Http404

    if request.method == "POST":
        group.delete()
        messages.success(request, "Successfully deleted group.")
        return redirect("eighth_admin_dashboard")
    else:
        context = {"admin_page_title": "Delete Group",
                   "item_name": str(group),
                   "help_text": "Deleting this group will remove all records "
                                "of it related to eighth period."}

        return render(request, "eighth/admin/delete_form.html", context)


@eighth_admin_required
def download_group_csv_view(request, group_id):
    try:
        group = Group.objects.get(id=group_id)
    except Group.DoesNotExist:
        raise http.Http404

    response = http.HttpResponse(content_type="text/csv")
    response[
        "Content-Disposition"] = "attachment; filename=\"{}.csv\"".format(group.name)

    writer = csv.writer(response)
    writer.writerow(
        ["Last Name", "First Name", "Student ID", "Grade", "Email"])
    users = group.user_set.all()
    users = sorted(users, key=lambda m: (m.last_name, m.first_name))
    for user in users:
        row = []
        row.append(user.last_name)
        row.append(user.first_name)
        row.append(user.student_id)
        grade = user.grade
        row.append(grade.number if grade else "Staff")
        emails = user.emails
        row.append(
            user.tj_email if user.tj_email else emails[0] if emails else None)
        writer.writerow(row)

    return response


class EighthAdminSignUpGroupWizard(SessionWizardView):
    FORMS = [("block", BlockSelectionForm),
             ("activity", ActivitySelectionForm)]

    TEMPLATES = {"block": "eighth/admin/sign_up_group.html",
                 "activity": "eighth/admin/sign_up_group.html"}

    def get_template_names(self):
        return [self.TEMPLATES[self.steps.current]]

    def get_form_kwargs(self, step):
        kwargs = {}
        if step == "block":
            kwargs.update(
                {"exclude_before_date": get_start_date(self.request)})
        if step == "activity":
            block = self.get_cleaned_data_for_step("block")["block"]
            kwargs.update({"block": block})

        labels = {"block": "Select a block", "activity": "Select an activity"}

        kwargs.update({"label": labels[step]})

        return kwargs

    def get_context_data(self, form, **kwargs):
        context = super(EighthAdminSignUpGroupWizard, self).get_context_data(
            form=form, **kwargs)

        block = self.get_cleaned_data_for_step("block")
        if block:
            context.update({"block_obj": block["block"]})

        context.update({"admin_page_title": "Sign Up Group"})
        return context

    def done(self, form_list, **kwargs):
        form_list = [f for f in form_list]
        block = form_list[0].cleaned_data["block"]
        activity = form_list[1].cleaned_data["activity"]
        scheduled_activity = EighthScheduledActivity.objects.get(
            block=block, activity=activity)

        try:
            group = Group.objects.get(id=kwargs["group_id"])
        except Group.DoesNotExist:
            raise http.Http404

        return redirect(reverse("eighth_admin_signup_group_action", args=[group.id, scheduled_activity.id]))


eighth_admin_signup_group = eighth_admin_required(
    EighthAdminSignUpGroupWizard.as_view(EighthAdminSignUpGroupWizard.FORMS))


def eighth_admin_signup_group_action(request, group_id, schact_id):

    try:
        scheduled_activity = EighthScheduledActivity.objects.get(id=schact_id)
        group = Group.objects.get(id=group_id)
    except (EighthScheduledActivity.DoesNotExist, Group.DoesNotExist):
        raise http.Http404

    users = group.user_set.all()

    if "confirm" in request.POST:
        for user in users:
            scheduled_activity.add_user(
                user, request, force=True, no_after_deadline=True)
        messages.success(request, "Successfully signed up group for activity.")
        return redirect("eighth_admin_dashboard")

    return render(request, "eighth/admin/sign_up_group.html", {"admin_page_title": "Confirm Group Signup",
                                                               "scheduled_activity": scheduled_activity,
                                                               "group": group,
                                                               "users_num": users.count()})


class EighthAdminDistributeGroupWizard(SessionWizardView):
    FORMS = [("block", BlockSelectionForm),
             ("activity", ScheduledActivityMultiSelectForm)]

    TEMPLATES = {"block": "eighth/admin/distribute_group.html",
                 "activity": "eighth/admin/distribute_group.html",
                 "choose": "eighth/admin/distribute_group.html"}

    def get_template_names(self):
        return [self.TEMPLATES[self.steps.current]]

    def dispatch(self, request, *args, **kwargs):
        self.group_id = kwargs.get('group_id', None)
        try:
            self.group = Group.objects.get(id=self.group_id)
        except Group.DoesNotExist:
            if self.request.resolver_match.url_name == "eighth_admin_distribute_unsigned":
                self.group = False
            else:
                raise http.Http404

        return super(EighthAdminDistributeGroupWizard, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self, step):
        kwargs = {}

        if step == "block":
            kwargs.update(
                {"exclude_before_date": get_start_date(self.request)})
        if step == "activity":
            logger.debug("cleaned block: {}".format(
                self.get_cleaned_data_for_step("block")["block"]))
            block = self.get_cleaned_data_for_step("block")
            if block:
                block = block["block"]
            kwargs.update({"block": block})

        labels = {"block": "Select a block",
                  "activity": "Select multiple activities"}

        kwargs.update({"label": labels[step]})

        return kwargs

    def get_context_data(self, form, **kwargs):
        context = super(EighthAdminDistributeGroupWizard, self).get_context_data(
            form=form, **kwargs)

        block = self.get_cleaned_data_for_step("block")

        if self.group:
            context.update({"group": self.group})
        elif block:
            unsigned = block["block"].get_unsigned_students()
            context.update({"users": unsigned, "eighthblock": block["block"]})

        if "block" in self.request.GET:
            block_id = self.request.GET["block"]
            context["redirect_block_id"] = block_id

        if self.request.resolver_match.url_name == "eighth_admin_distribute_unsigned":
            context.update({"users_type": "unsigned"})
            context.update({"group": False})

        context.update(
            {"admin_page_title": "Distribute Group Members Among Activities"})
        return context

    def done(self, form_list, **kwargs):
        form_list = [f for f in form_list]
        block = form_list[0].cleaned_data["block"]
        activities = form_list[1].cleaned_data["activities"]

        logger.debug(block)
        logger.debug(activities)

        schact_ids = []
        for act in activities:
            try:
                schact = EighthScheduledActivity.objects.get(
                    block=block, activity=act)
                schact_ids.append(schact.id)
            except EighthScheduledActivity.DoesNotExist:
                raise http.Http404

        args = ""
        for said in schact_ids:
            args += "&schact={}".format(said)

        if "group_id" in kwargs:
            gid = kwargs["group_id"]
            args += "&group={}".format(gid)

        if self.request.resolver_match.url_name == "eighth_admin_distribute_unsigned":
            args += "&unsigned=1&block={}".format(block.id)

        return redirect("/eighth/admin/groups/distribute_action?{}".format(args))


eighth_admin_distribute_group = eighth_admin_required(
    EighthAdminDistributeGroupWizard.as_view(EighthAdminDistributeGroupWizard.FORMS))

eighth_admin_distribute_unsigned = eighth_admin_required(
    EighthAdminDistributeGroupWizard.as_view(EighthAdminDistributeGroupWizard.FORMS))


@eighth_admin_required
def eighth_admin_distribute_action(request):
    if "users" in request.POST:
        logger.debug(request.POST)
        activity_user_map = {}
        for item in request.POST:
            if item[:6] == "schact":
                try:
                    sid = int(item[6:])
                    schact = EighthScheduledActivity.objects.get(id=sid)
                except EighthScheduledActivity.DoesNotExist:
                    messages.error(
                        request, "ScheduledActivity does not exist with id {}".format(sid))

                userids = request.POST.getlist(item)
                activity_user_map[schact] = userids

        changes = 0
        logger.debug(activity_user_map)
        for schact, userids in activity_user_map.items():
            for uid in userids:
                changes += 1
                schact.add_user(
                    User.objects.get(id=int(uid)), request=None, force=True, no_after_deadline=True)

        messages.success(
            request, "Successfully completed {} activity signups.".format(changes))

        return redirect("eighth_admin_dashboard")
    elif "schact" in request.GET:
        schactids = request.GET.getlist("schact")

        schacts = []
        for schact in schactids:
            try:
                sch = EighthScheduledActivity.objects.get(id=schact)
                schacts.append(sch)
            except EighthScheduledActivity.DoesNotExist:
                raise http.Http404

        users = []
        users_type = ""

        if "group" in request.GET:
            group = Group.objects.get(id=request.GET.get("group"))
            users = group.user_set.all()
            users_type = "group"
        elif "unsigned" in request.GET:
            unsigned = []

            if "block" in request.GET:
                blockid = request.GET.get("block")
                block = EighthBlock.objects.get(id=blockid)
            else:
                raise http.Http404

            unsigned = User.objects.get_students().exclude(
                eighthsignup__scheduled_activity__block__id=blockid)

            users = unsigned
            users_type = "unsigned"

            if "limit" in request.GET:
                users = users[0:int(request.GET.get('limit'))]

        # Sort by last name
        users = sorted(list(users), key=lambda x: x.last_name)

        context = {
            "admin_page_title": "Distribute Group Members Across Activities",
            "users_type": users_type,
            "group": group if users_type == "group" else None,
            "eighthblock": block if users_type == "unsigned" else None,
            "schacts": schacts,
            "users": users,
            "show_selection": True
        }

        return render(request, "eighth/admin/distribute_group.html", context)
    else:
        return redirect("eighth_admin_dashboard")


@eighth_admin_required
def add_member_to_group_view(request, group_id):
    if request.method != "POST":
        return http.HttpResponseNotAllowed(["POST"], "HTTP 405: METHOD NOT ALLOWED")

    try:
        group = Group.objects.get(id=group_id)
    except Group.DoesNotExist:
        raise http.Http404

    next_url = reverse(
        "eighth_admin_edit_group", kwargs={"group_id": group_id})

    if "user_id" in request.POST:
        user_ids = request.POST.getlist("user_id")
        user_objects = User.objects.filter(id__in=user_ids)
        next_url += "?"
        for user in user_objects:
            user.groups.add(group)
            user.save()
            if len(user_objects) < 25:
                next_url += "added={}&".format(user.id)
        invalidate_obj(group)
        messages.success(request, "Successfully added {} user{} to the group.".format(
            len(user_objects), "s" if len(user_objects) != 1 else ""))
        return redirect(next_url)

    if "query" not in request.POST:
        return redirect(next_url + "?error=s")

    query = request.POST["query"]
    from_sid = User.objects.user_with_student_id(query)
    if from_sid:
        from_sid.groups.add(group)
        from_sid.save()
        messages.success(
            request, "Successfully added user \"{}\" to the group.".format(from_sid.full_name))
        return redirect(next_url + "?added=" + str(from_sid.id))

    errors, results = get_search_results(query)
    logger.debug(results)
    if len(results) == 1:
        user_id = results[0].id
        logger.debug("User id: {}".format(user_id))
        user = User.objects.user_with_ion_id(user_id)

        user.groups.add(group)
        user.save()
        messages.success(
            request, "Successfully added user \"{}\" to the group.".format(user.full_name))
        return redirect(next_url + "?added=" + str(user_id))
    elif len(results) == 0:
        return redirect(next_url + "?error=n")
    else:
        users = results
        results = sorted(results, key=lambda x: (x.last_name, x.first_name))
        context = {"query": query, "users": users, "group": group,
                   "admin_page_title": "Add Members to Group"}
        return render(request, "eighth/admin/possible_students_add_group.html", context)


@eighth_admin_required
def remove_member_from_group_view(request, group_id, user_id):
    if request.method != "POST":
        return http.HttpResponseNotAllowed(["POST"], "HTTP 405: METHOD NOT ALLOWED")

    try:
        group = Group.objects.get(id=group_id)
    except Group.DoesNotExist:
        raise http.Http404

    uid = request.POST.get("profile_id", 0)
    if uid:
        next_url = reverse("user_profile", args=(uid,))
    else:
        next_url = reverse(
            "eighth_admin_edit_group", kwargs={"group_id": group_id})

    try:
        user = User.get_user(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "There was an error removing this user.")
        return redirect(next_url, status=400)

    group.user_set.remove(user)
    group.save()
    invalidate_obj(group)
    messages.success(
        request, "Successfully removed user \"{}\" from the group.".format(user.full_name))

    return redirect(next_url)
