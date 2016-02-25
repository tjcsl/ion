# -*- coding: utf-8 -*-

import logging

from django import http
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import LDAPCourse

logger = logging.getLogger(__name__)


@login_required
def main_view(request):
    """Show the current user's class schedule."""

    user = request.user
    courses = user.ionldap_courses

    context = {
        "user": user,
        "courses": courses
    }

    return render(request, "ionldap/main.html", context)

@login_required
def class_section_view(request, section_id):
    try:
        course = LDAPCourse.objects.get(section_id=section_id)
    except LDAPCourse.DoesNotExist:
        raise http.Http404

    in_class = (course.users.filter(id=request.user.id).count() == 1)
    can_view_students = (request.user.is_teacher)# or request.user.is_eighth_admin)
    teacher_classes = LDAPCourse.objects.filter(teacher_name=course.teacher_name)
    section_classes = LDAPCourse.objects.filter(course_id=course.course_id)

    context = {
        "course": course,
        "in_class": in_class,
        "can_view_students": can_view_students,
        "teacher_user": course.teacher_user,
        "teacher_classes": teacher_classes,
        "section_classes": section_classes
    }

    return render(request, "ionldap/class.html", context)

@login_required
def class_room_view(request, room_id):
    courses = LDAPCourse.objects.filter(room_name="{}".format(room_id))

    context = {
        "room": room_id,
        "courses": courses
    }

    return render(request, "ionldap/class_room.html", context)

@login_required
def all_classes_view(request):
    pass