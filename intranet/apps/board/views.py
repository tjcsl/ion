# -*- coding: utf-8 -*-

import logging
from django import http
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from ..ionldap.models import LDAPCourse
from .models import Board, BoardPost, BoardPostComment
from .forms import BoardPostForm, BoardPostCommentForm

logger = logging.getLogger(__name__)


def can_view_board(request, course_id=None, section_id=None):
    #if request.user.has_admin_permission("board"):
    #    return True
    if course_id:
        return request.user.ionldap_courses.filter(course_id=course_id).count() > 0
    elif section_id:
        return request.user.ionldap_courses.filter(section_id=section_id).count() > 0




@login_required
def home(request):
    """The homepage, showing all board posts available to you."""

    classes = request.user.ionldap_courses or []
    section_ids = [c.section_id for c in classes]
    posts = BoardPost.objects.filter(board__section_id__in=section_ids)

    context = {
        "classes": classes,
        "posts": posts
    }

    return render(request, "board/home.html", context)

def get_user_section(user, course_id):
    classes = user.ionldap_courses
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
        board = Board.objects.get(course_id=course_id)
    except Board.DoesNotExist:
        # Create a board for this class
        board = Board.objects.create(course_id=course_id)

    if not board.has_member(request.user):
        return render(request, "board/error.html", {"reason": "You are not a member of this course."}, status=403)
    else:
        my_section = get_user_section(request.user, course_id)

    posts = BoardPost.objects.filter(board__course_id=course_id)

    posts |= BoardPost.objects.filter(board__section_id=my_section.section_id)

    context = {
        "board": board,
        "type": "course",
        "course_id": course_id,
        "course_title": course_title,
        "ldap_courses": ldap_courses,
        "my_section": my_section,
        "posts": posts
    }

    return render(request, "board/feed.html", context)


@login_required
def section_feed(request, section_id):
    """The feed of a section."""

    try:
        section = LDAPCourse.objects.get(section_id=section_id)
    except LDAPCourse.DoesNotExist:
        return render(request, "board/error.html", {"reason": "This class doesn't exist."}, status=404)

    try:
        board = Board.objects.get(section_id=section_id)
    except Board.DoesNotExist:
        # Create a board for this class
        board = Board.objects.create(section_id=section_id)

    if not board.has_member(request.user):
        return render(request, "error/403.html", {"reason": "You are not a member of this class."}, status=403)

    context = {
        "board": board,
        "type": "section",
        "section_id": section_id,
        "section": section,
        "posts": BoardPost.objects.filter(board__section_id=section_id)
    }

    return render(request, "board/feed.html", context)


@login_required
def course_feed_post(request, course_id):
    """Post to course feed."""

    ldap_courses = LDAPCourse.objects.filter(course_id=course_id)

    course_title = ldap_courses[0].course_title

    try:
        board = Board.objects.get(course_id=course_id)
    except Board.DoesNotExist:
        # Create a board for this class
        board = Board.objects.create(course_id=course_id)

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
            return redirect("board_class", course_id)
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
def section_feed_post(request, section_id):
    """Post to class feed."""

    try:
        section = LDAPCourse.objects.get(section_id=section_id)
    except LDAPCourse.DoesNotExist:
        return render(request, "board/error.html", {"reason": "This class doesn't exist."}, status=404)

    try:
        board = Board.objects.get(section_id=section_id)
    except Board.DoesNotExist:
        # Create a board for this class
        board = Board.objects.create(section_id=section_id)

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
            return redirect("board_section", section_id)
        else:
            messages.error(request, "Error adding post")
    else:
        form = BoardPostForm()

    context = {
        "form": form,
        "action": "add",
        "section": section,
        "board": board
    }
    return render(request, "board/add_modify.html", context)


@login_required
def modify_post_view(request, id=None):

    """Modify post page. You may only modify an event if you were the creator or you are an
    administrator.

    id: post id

    """
    if ONLY_REACTIONS:
        return redirect("board")

    post = get_object_or_404(BoardPost, id=id)

    if not request.user.has_admin_permission('board') and post.user != request.user:
        return render(request, "board/error.html", {"reason": "You are neither this event's creator or an administrator."}, status=403)

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
def delete_post_view(request, id=None):

    """Delete post page. You may only delete a post if you were the creator or you are an
    administrator.

    id: post id

    """
    post = get_object_or_404(BoardPost, id=id)

    if not request.user.has_admin_permission('board') and post.user != request.user:
        return render(request, "board/error.html", {"reason": "You are neither this event's creator or an administrator."}, status=403)

    if request.method == "POST" and "confirm" in request.POST:
        post.delete()
        messages.success(request, "Deleted post.")
        return redirect("board")
    else:
        return render(request, "board/delete.html", {"post": post})


@login_required
def comment_view(request, post_id):
    """Add a comment form page."""
    if ONLY_REACTIONS:
        return redirect("board")

    post = get_object_or_404(BoardPost, id=post_id)
    board = post.board

    if not board.has_member(request.user):
        return render(request, "board/error.html", {"reason": "You are not allowed to view the board in which this post resides."}, status=403)

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

@login_required
def delete_comment_view(request, id=None):

    """Delete comment page. You may only delete a comment if you were the creator or you are an
    administrator.

    id: comment id

    """
    comment = get_object_or_404(BoardPostComment, id=id)
    post = comment.post

    if not request.user.has_admin_permission('board') and comment.user != request.user:
        return render(request, "board/error.html", {"reason": "You are neither this event's creator or an administrator."}, status=403)

    if request.method == "POST" and "confirm" in request.POST:
        comment.delete()
        messages.success(request, "Deleted comment.")
        return http.HttpResponse("Deleted comment.")
    else:
        return http.HttpResponseNotAllowed(["POST"], "HTTP 405: METHOD NOT ALLOWED")

@login_required
def view_post(request, post_id):
    post = get_object_or_404(BoardPost, id=post_id)
    board = post.board

    if not board.has_member(request.user):
        return render(request, "error/403.html", {"reason": "You are not allowed to view the board in which this post resides."}, status=403)

    context = {
        "post": post,
        "board": board
    }

    if board.type == "section":
        context["section"] = board.section_obj
    elif board.type == "course":
        context["course_id"] = board.course_id

    return render(request, "board/view.html", context)

@login_required
def react_post_view(request, id=None):

    """

    id: post id

    """
    post = get_object_or_404(BoardPost, id=id)
    board = post.board


    if not board.has_member(request.user):
        return http.HttpResponseNotAllowed(["POST"], "Invalid permissions.")

    reactions = post.comments.filter(user=request.user)
    if reactions.count() > 0:
        reactions.delete()
    
    reaction = request.POST.get("reaction", None)

    if request.method == "POST" and reaction:
        allowed_reactions = [str(i) for i in range(1,7)]
        allowed_reactions += ["stallman"]

        if reaction not in allowed_reactions:
            reaction = "1"

        content = '<div class="reaction-icon comment-reaction reaction-{}"></div>'.format(reaction)
        if reaction == "stallman":
            content += "I'd just like to interject for moment. What you're refering to as Linux, is in fact, GNU/Linux, or as I've recently taken to calling it, GNU plus Linux."

        obj = BoardPostComment.objects.create(content=content, safe_html=True, user=request.user)
        post.comments.add(obj)
        post.save()
        messages.success(request, "Reaction added")
        return http.HttpResponse("Reaction added")
    else:
        return http.HttpResponseNotAllowed(["POST"], "HTTP 405: METHOD NOT ALLOWED")
    