# -*- coding: utf-8 -*-

from django.contrib import admin

from .models import Board, BoardPost, BoardPostComment

admin.site.register([Board, BoardPost, BoardPostComment])
