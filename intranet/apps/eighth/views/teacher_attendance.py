# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render


def eighth_teacher_index_view(request):
    return render(request, "eighth/teacher.html")


def eighth_teacher_attendance_view(request):
    return render(request, "eighth/teacher.html")
