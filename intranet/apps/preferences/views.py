# -*- coding: utf-8 -*-

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .forms import (NotificationOptionsForm, PreferredPictureForm, PrivacyOptionsForm, PhoneFormset, EmailFormset, WebsiteFormset)
from ..users.models import User, Email

logger = logging.getLogger(__name__)


def get_personal_info(user):
    """Get a user's personal info attributes to pass as an initial value to a
    PersonalInformationForm."""
    # change this to not use other_phones
    num_phones = len(user.phones.all() or [])
    num_emails = len(user.emails.all() or [])
    num_websites = len(user.websites.all() or [])

    personal_info = {}

    for i in range(num_phones):
        personal_info["phone_{}".format(i)] = user.phones.all()[i]

    for i in range(num_emails):
        personal_info["email_{}".format(i)] = user.emails.all()[i]

    for i in range(num_websites):
        personal_info["website_{}".format(i)] = user.websites.all()[i]

    num_fields = {"phones": num_phones, "emails": num_emails, "websites": num_websites}

    return personal_info, num_fields


def save_personal_info(request, user):
    phone_formset = PhoneFormset(request.POST, instance=user, prefix='pf')
    email_formset = EmailFormset(request.POST, instance=user, prefix='ef')
    website_formset = WebsiteFormset(request.POST, instance=user, prefix='wf')

    errors = []

    if phone_formset.is_valid():
        phone_formset.save()
    else:
        errors.append('Could not set phone numbers.')
    if email_formset.is_valid():
        email_formset.save()
    else:
        errors.append('Could not set emails.')
    if website_formset.is_valid():
        website_formset.save()
    else:
        errors.append('Could not set websites.')

    return phone_formset, email_formset, website_formset, errors


def get_preferred_pic(user):
    """Get a user's preferred picture attributes to pass as an initial value to a
    PreferredPictureForm."""

    # FIXME: remove this hardcoded junk
    preferred_pic = {"preferred_photo": "AUTO"}
    if user.preferred_photo:
        preferred_pic["preferred_photo"] = user.preferred_photo.grade_number

    return preferred_pic


def save_preferred_pic(request, user):
    preferred_pic = get_preferred_pic(user)
    logger.debug(preferred_pic)
    preferred_pic_form = PreferredPictureForm(user, data=request.POST, initial=preferred_pic)
    if preferred_pic_form.is_valid():
        logger.debug("Preferred pic form: valid")
        if preferred_pic_form.has_changed():
            fields = preferred_pic_form.cleaned_data
            logger.debug(fields)
            if "preferred_photo" in fields:
                # These aren't actually the Photos, these are the grade_numbers of the Photos
                new_preferred_pic = fields["preferred_photo"]
                old_preferred_pic = preferred_pic["preferred_photo"] if preferred_pic else None
                if old_preferred_pic == new_preferred_pic:
                    logger.debug("{}: same ({})".format("preferred_photo", new_preferred_pic))
                else:
                    logger.debug("{}: new: {} from: {}".format("preferred_photo",
                                                               new_preferred_pic, old_preferred_pic if "preferred_photo" in preferred_pic else None))
                    try:
                        user.preferred_photo = user.photos.filter(grade_number=new_preferred_pic)
                    except Exception as e:
                        messages.error(request, "Unable to set field {} with value {}: {}".format("preferred_pic", new_preferred_pic, e))
                        logger.debug("Unable to set field {} with value {}: {}".format("preferred_pic", new_preferred_pic, e))
                    else:
                        messages.success(request, "Set field {} to {}".format("preferred_pic",
                                                                              new_preferred_pic if not isinstance(new_preferred_pic, list) else
                                                                              ", ".join(new_preferred_pic)))
    return preferred_pic_form


def get_privacy_options(user):
    """Get a user's privacy options to pass as an initial value to a PrivacyOptionsForm."""

    privacy_options = {}

    for ptype in user.permissions:
        for field in user.permissions[ptype]:
            if ptype == "self":
                privacy_options["{}-{}".format(field, ptype)] = user.permissions[ptype][field]
            else:
                privacy_options[field] = user.permissions[ptype][field]

    return privacy_options


def save_privacy_options(request, user):
    privacy_options = get_privacy_options(user)
    logger.debug(privacy_options)
    privacy_options_form = PrivacyOptionsForm(user, data=request.POST, initial=privacy_options)
    if privacy_options_form.is_valid():
        logger.debug("Privacy options form: valid")
        if privacy_options_form.has_changed():
            fields = privacy_options_form.cleaned_data
            logger.debug("Privacy form fields:")
            logger.debug(fields)
            for field in fields:
                if field in privacy_options and privacy_options[field] == fields[field]:
                    logger.debug("{}: same ({})".format(field, fields[field]))
                else:
                    logger.debug("{}: new: {} from: {}".format(field, fields[field], privacy_options[field] if field in privacy_options else None))
                    try:
                        if field.endswith("-self"):
                            field_name = field.split("-self")[0]
                            field_type = "self"
                        elif field.endswith("self"):
                            field_name = field.split("self")[0]
                            field_type = "self"
                        else:
                            field_name = field
                            field_type = "parent"
                        if field_type == "self":
                            success = user.properties.set_permission(field_name, fields[field], admin=request.user.is_eighth_admin)
                        elif request.user.is_eighth_admin:
                            success = user.properties.set_permission(field_name, fields[field], parent=True, admin=True)
                        else:
                            raise Exception("You do not have permission to change this parent field.")
                        if not success:
                            raise Exception("You cannot override the parent field.")
                    except Exception as e:
                        messages.error(request, "Unable to set field {} with value {}: {}".format(field, fields[field], e))
                        logger.debug("Unable to set field {} with value {}: {}".format(field, fields[field], e))
                    else:
                        messages.success(request, "Set field {} to {}".format(field, fields[field]
                                                                              if not isinstance(fields[field], list) else ", ".join(fields[field])))
    return privacy_options_form


def get_notification_options(user):
    """Get a user's notification options to pass as an initial value to a
    NotificationOptionsForm."""

    notification_options = {}
    notification_options["receive_news_emails"] = user.receive_news_emails
    notification_options["receive_eighth_emails"] = user.receive_eighth_emails
    try:
        notification_options["primary_email"] = user.primary_email
    except Email.DoesNotExist:
        user.primary_email = None
        user.save()
        notification_options["primary_email"] = None

    return notification_options


def save_notification_options(request, user):
    notification_options = get_notification_options(user)
    logger.debug(notification_options)
    notification_options_form = NotificationOptionsForm(user, data=request.POST, initial=notification_options)
    if notification_options_form.is_valid():
        logger.debug("Notification options form: valid")
        if notification_options_form.has_changed():
            fields = notification_options_form.cleaned_data
            logger.debug("Fields: {}".format(fields))
            for field in fields:
                if field in notification_options and notification_options[field] == fields[field]:
                    logger.debug("{}: same ({})".format(field, fields[field]))
                else:
                    logger.debug("{}: new: {} from: {}".format(field, fields[field], notification_options[field]
                                                               if field in notification_options else None))
                    setattr(user, field, fields[field])
                    user.save()
                    try:
                        messages.success(request, "Set field {} to {}".format(field, fields[field]
                                                                              if not isinstance(fields[field], list) else ", ".join(fields[field])))
                    except TypeError:
                        pass
    return notification_options_form


def save_gcm_options(request, user):
    if request.user.notificationconfig and request.user.notificationconfig.gcm_token:
        receive = ("receive_push_notifications" in request.POST)
        if receive:
            nc = user.notificationconfig
            if nc.gcm_optout is True:
                nc.gcm_optout = False
                nc.save()
                messages.success(request, "Enabled push notifications")
        else:
            nc = user.notificationconfig
            if nc.gcm_optout is False:
                nc.gcm_optout = True
                nc.save()
                messages.success(request, "Disabled push notifications")


@login_required
def preferences_view(request):
    """View and process updates to the preferences page."""
    user = request.user

    if request.method == "POST":
        logger.debug(dict(request.POST))
        phone_formset, email_formset, website_formset, errors = save_personal_info(request, user)
        if user.is_student:
            preferred_pic_form = save_preferred_pic(request, user)
        else:
            preferred_pic_form = None
        privacy_options_form = save_privacy_options(request, user)
        notification_options_form = save_notification_options(request, user)

        for error in errors:
            messages.error(request, error)

        try:
            save_gcm_options(request, user)
        except AttributeError:
            pass

        return redirect("preferences")

    else:
        phone_formset = PhoneFormset(instance=user, prefix='pf')
        email_formset = EmailFormset(instance=user, prefix='ef')
        website_formset = WebsiteFormset(instance=user, prefix='wf')

        if user.is_student:
            preferred_pic = get_preferred_pic(user)
            logger.debug(preferred_pic)
            preferred_pic_form = PreferredPictureForm(user, initial=preferred_pic)
        else:
            preferred_pic = None
            preferred_pic_form = None

        privacy_options = get_privacy_options(user)
        logger.debug(privacy_options)
        privacy_options_form = PrivacyOptionsForm(user, initial=privacy_options)

        notification_options = get_notification_options(user)
        logger.debug(notification_options)
        notification_options_form = NotificationOptionsForm(user, initial=notification_options)

    context = {
        "phone_formset": phone_formset,
        "email_formset": email_formset,
        "website_formset": website_formset,
        "preferred_pic_form": preferred_pic_form,
        "privacy_options_form": privacy_options_form,
        "notification_options_form": notification_options_form,
    }
    return render(request, "preferences/preferences.html", context)


@login_required
def privacy_options_view(request):
    """View and edit privacy options for a user."""
    if "user" in request.GET:
        user = User.objects.get(id=request.GET.get("user"))
    elif "student_id" in request.GET:
        user = User.objects.user_with_student_id(request.GET.get("student_id"))
    else:
        user = request.user

    if not user:
        messages.error(request, "Invalid user.")
        user = request.user

    if request.method == "POST":
        privacy_options_form = save_privacy_options(request, user)
    else:
        privacy_options = get_privacy_options(user)
        privacy_options_form = PrivacyOptionsForm(user, initial=privacy_options)

    context = {"privacy_options_form": privacy_options_form, "profile_user": user}
    return render(request, "preferences/privacy_options.html", context)
