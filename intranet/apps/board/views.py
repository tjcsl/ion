# -*- coding: utf-8 -*-

import logging
from django import http
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from ..ionldap.models import LDAPCourse
from .models import Board, BoardPost
from .forms import BoardPostForm, BoardPostCommentForm

logger = logging.getLogger(__name__)


def can_view_boards(request, course_id=None):
    return request.user.has_admin_permission("board")


@login_required
def home(request):
    if not can_view_boards(request):
        return redirect("/")

    """The homepage, showing all board posts available to you."""

    classes = request.user.ionldap_courses or []
    class_ids = [c.class_id for c in classes]
    posts = BoardPost.objects.filter(board__class_id__in=class_ids)

    context = {
        "classes": classes,
        "posts": posts
    }

    return render(request, "board/home.html", context)

def get_user_section(user, course_id):
    classes = request.user.ionldap_courses
    if classes:
        sect = classes.filter(course_id=course_id)
        if sect:
            return sect.first()


@login_required
def course_feed(request, course_id):
    if not can_view_board(request, course_id=course_id):
        return redirect("/")

    """The feed of a course (which contains multiple classes)."""
    ldap_courses = LDAPCourse.objects.filter(course_id=course_id)
    
    if ldap_courses.count() == 0:
        # The course doesn't actually exist
        return render(request, "board/error.html", {"reason": "This course doesn't exist."}, status=404)

    course_title = ldap_courses[0].course_title

    try:
        board = Board.objects.get(class_id=course_id)
    except Board.DoesNotExist:
        # Create a board for this class
        board = Board.objects.create(class_id=course_id)

    if not board.has_member(request.user):
        return render(request, "board/error.html", {"reason": "You are not a member of this course."}, status=403)
    else:
        my_class = get_user_section(request.user, course_id)

    posts = BoardPost.objects.filter(board__class_id=course_id)

    posts |= BoardPost.objects.filter(board__class_id=my_course.class_id)

    context = {
        "board": board,
        "type": "course",
        "course_id": course_id,
        "course_title": course_title,
        "ldap_courses": ldap_courses,
        "my_class": my_class,
        "posts": posts
    }

    return render(request, "board/feed.html", context)


@login_required
def section_feed(request, class_id):
    if not can_view_boards(request):
        return redirect("/")

    """The feed of a section."""

    try:
        class_obj = LDAPCourse.objects.get(class_id=class_id)
    except LDAPCourse.DoesNotExist:
        return render(request, "board/error.html", {"reason": "This class doesn't exist."}, status=404)

    try:
        board = Board.objects.get(class_id=class_id)
    except Board.DoesNotExist:
        # Create a board for this class
        board = Board.objects.create(class_id=class_id)

    if not board.has_member(request.user):
        return render(request, "error/403.html", {"reason": "You are not a member of this class."}, status=403)

    context = {
        "board": board,
        "type": "class",
        "class_id": class_id,
        "class_obj": class_obj,
        "posts": BoardPost.objects.filter(board__class_id=class_id)
    }

    return render(request, "board/feed.html", context)


@login_required
def course_feed_post(request, class_id):
    if not can_view_boards(request, course_id=course_id):
        return redirect("/")

    """Post to course feed."""

    ldap_courses = LDAPCourse.objects.filter(course_id=course_id)

    course_title = ldap_courses[0].course_title

    try:
        board = Board.objects.get(class_id=course_id)
    except Board.DoesNotExist:
        # Create a board for this class
        board = Board.objects.create(class_id=course_id)

    if not board.has_member(request.user):
        return render(request, "error/403.html", {"reason": "You are not a member of this class."}, status=403)

    if request.method == "POST":
        form = BoardPostForm(request.POST)
        logger.debug(form)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()

            board.posts.add(obj)
            board.save()

            messages.success(request, "Successfully added post.")
            return redirect("board_class", class_id=class_id)
        else:
            messages.error(request, "Error adding post")
    else:
        form = BoardPostForm()

    context = {
        "form": form,
        "action": "add",
        "ldap_courses": ldap_courses,
        "course_title": course_title,
        "board": board
    }
    return render(request, "board/add_modify.html", context)


@login_required
def section_feed_post(request, class_id):
    if not can_view_boards(request):
        return redirect("/")

    """Post to class feed."""

    try:
        class_obj = LDAPCourse.objects.get(class_id=class_id)
    except LDAPCourse.DoesNotExist:
        return render(request, "board/error.html", {"reason": "This class doesn't exist."}, status=404)

    try:
        board = Board.objects.get(class_id=class_id)
    except Board.DoesNotExist:
        # Create a board for this class
        board = Board.objects.create(class_id=class_id)

    if not board.has_member(request.user):
        return render(request, "error/403.html", {"reason": "You are not a member of this class."}, status=403)

    if request.method == "POST":
        form = BoardPostForm(request.POST)
        logger.debug(form)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()

            board.posts.add(obj)
            board.save()

            messages.success(request, "Successfully added post.")
            return redirect("board_section", args=(class_id,))
        else:
            messages.error(request, "Error adding post")
    else:
        form = BoardPostForm()

    context = {
        "form": form,
        "action": "add",
        "class_obj": class_obj,
        "board": board
    }
    return render(request, "board/add_modify.html", context)


@login_required
def modify_post_view(request, id=None):
    if not can_view_boards(request):
        return redirect("/")

    """Modify post page. You may only modify an event if you were the creator or you are an
    administrator.

    id: post id

    """
    post = get_object_or_404(BoardPost, id=id)

    if not request.user.has_admin_permission('board') and post.user != request.user:
        return render(request, "error/403.html", {"reason": "You are neither this event's creater or an administrator."}, status=403)

    if request.method == "POST":
        form = BoardPostForm(request.POST, instance=post)
        logger.debug(form)
        if form.is_valid():
            obj = form.save()
            obj.user = request.user
            obj.save()
            messages.success(request, "Successfully modified post.")
            # return redirect("events")
        else:
            messages.error(request, "Error adding post.")
    else:
        form = BoardPostForm(instance=post)
    return render(request, "board/add_modify.html", {"form": form, "action": "modify", "id": id})


@login_required
def comment_view(request, post_id):
    if not can_view_boards(request):
        return redirect("/")

    """Add a comment form page."""

    post = get_object_or_404(BoardPost, id=post_id)
    board = post.board

    if not board.has_member(request.user):
        return render(request, "error/403.html", {"reason": "You are not alloed to view this board."}, status=403)

    if request.method == "POST":
        form = BoardPostCommentForm(request.POST)
        logger.debug(form)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()

            post.comments.add(obj)
            post.save()

            messages.success(request, "Successfully added comment.")
            return redirect("board")
        else:
            messages.error(request, "Error adding post")
    else:
        form = BoardPostCommentForm()

    context = {
        "form": form,
        "action": "add",
        "post": post,
        "board": board
    }
    return render(request, "board/comment.html", context)
