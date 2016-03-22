# -*- coding: utf-8 -*-

import logging
from django import http
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from ..users.models import Class, ClassSections
from .models import Board, BoardPost
from .forms import BoardPostForm, BoardPostCommentForm

logger = logging.getLogger(__name__)


@login_required
def home(request):
    """The homepage, showing all board posts available to you."""

    classes = request.user.classes or []
    section_ids = [c.section_id for c in classes]
    posts = BoardPost.objects.filter(board__class_id__in=section_ids)

    context = {
        "posts": posts
    }

    return render(request, "board/home.html", context)


@login_required
def class_feed(request, class_id):
    """The feed of a class."""
    class_obj = Class(id=class_id)
    if class_obj.name is None:
        # The class doesn't actually exist
        raise http.Http404

    try:
        board = Board.objects.get(class_id=class_id)
    except Board.DoesNotExist:
        # Create a board for this class
        board = Board.objects.create(class_id=class_id)

    if not board.has_member(request.user):
        return render(request, "error/403.html", {"reason": "You are not a member of this class."}, status=403)

    posts = BoardPost.objects.filter(board__class_id=class_id)

    posts |= BoardPost.objects.filter(board__section_id=class_obj.class_id)

    context = {
        "board": board,
        "type": "class",
        "class_id": class_id,
        "class_obj": class_obj,
        "posts": posts
    }

    return render(request, "board/feed.html", context)


@login_required
def section_feed(request, section_id):
    """The feed of a section."""

    # Check permissions
    try:
        section = ClassSections(id=section_id)
        classes = section.classes
        if len(classes) < 1:
            raise http.Http404

    except Exception:
        raise http.Http404

    try:
        board = Board.objects.get(section_id=section_id)
    except Board.DoesNotExist:
        # Create a board for this class
        board = Board.objects.create(section_id=section_id)

    if not board.has_member(request.user):
        return render(request, "error/403.html", {"reason": "You are not a member of this section."}, status=403)

    context = {
        "board": board,
        "type": "section",
        "section_id": section_id,
        "section": section,
        "posts": BoardPost.objects.filter(board__section_id=section_id)
    }

    return render(request, "board/feed.html", context)


@login_required
def class_feed_post(request, class_id):
    """Post to class feed."""

    # Check permissions
    class_obj = Class(id=class_id)
    if class_obj.name is None:
        # The class doesn't actually exist
        raise http.Http404

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
            return redirect("board_class", args=(class_id,))
        else:
            messages.error(request, "Error adding post")
    else:
        form = BoardPostForm()
    context = {
        "form": form,
        "action": "add",
        "class": class_obj,
        "board": board
    }
    return render(request, "board/add_modify.html", context)


@login_required
def section_feed_post(request, section_id):
    """Post to section feed."""

    # Check permissions
    try:
        section = ClassSections(id=section_id)
        classes = section.classes
        if len(classes) < 1:
            raise http.Http404

    except Exception:
        raise http.Http404

    try:
        board = Board.objects.get(section_id=section_id)
    except Board.DoesNotExist:
        # Create a board for this class
        board = Board.objects.create(section_id=section_id)

    if not board.has_member(request.user):
        return render(request, "error/403.html", {"reason": "You are not a member of this section."}, status=403)

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
            return redirect("board_section", args=(section_id,))
        else:
            messages.error(request, "Error adding post")
    else:
        form = BoardPostForm()

    context = {
        "form": form,
        "action": "add",
        "section": section,
        "classes": classes,
        "board": board
    }
    return render(request, "board/add_modify.html", context)


@login_required
def modify_post_view(request, id=None):
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
