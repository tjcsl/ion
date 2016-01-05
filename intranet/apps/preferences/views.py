# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from ...db.ldap_db import LDAPConnection
from ..users.models import User
from .forms import (
    PersonalInformationForm, PreferredPictureForm, PrivacyOptionsForm, NotificationOptionsForm
)

import logging

logger = logging.getLogger(__name__)


def get_personal_info(user):
    """Get a user's personal info attributes to pass as an initial
       value to a PersonalInformationForm
    """
    # number of additional phones (other_phones)
    num_phones = len(user.other_phones or [])
    num_emails = len(user.emails or [])
    num_webpages = len(user.webpages or [])

    personal_info = {
        "mobile_phone": user.mobile_phone,
        "home_phone": user.home_phone
    }

    for i in range(num_phones):
        personal_info["other_phone_{}".format(i)] = user.other_phones[i]

    for i in range(num_emails):
        personal_info["email_{}".format(i)] = user.emails[i]

    for i in range(num_webpages):
        personal_info["webpage_{}".format(i)] = user.webpages[i]

    num_fields = {
        "phones": num_phones,
        "emails": num_emails,
        "webpages": num_webpages
    }

    return personal_info, num_fields


def save_personal_info(request, user):
    personal_info, _num_fields = get_personal_info(user)
    num_fields = {
        "phones": sum([1 if "other_phone_" in name else 0 for name in request.POST]),
        "emails": sum([1 if "email_" in name else 0 for name in request.POST]),
        "webpages": sum([1 if "webpage_" in name else 0 for name in request.POST])
    }
    logger.debug(num_fields)
    logger.debug(request.POST)
    personal_info_form = PersonalInformationForm(num_fields=num_fields, data=request.POST, initial=personal_info)
    logger.debug(personal_info_form)
    if personal_info_form.is_valid():
        logger.debug("Personal info: valid")
        
        # form.has_changed() will not report a change if a field is missing
        num_fields_changed = False
        for f in num_fields:
            if num_fields[f] != _num_fields[f]:
                num_fields_changed = True

        if personal_info_form.has_changed() or num_fields_changed:
            logger.debug("Personal info: changed")
            fields = personal_info_form.cleaned_data
            logger.debug(fields)

            # add None value for fields missing
            for f in _num_fields:
                # remove "s" from end of field name
                fld = f[:-1]
                fld_num_max = _num_fields[f]
                for fld_num in range(0, fld_num_max):
                    fld_name = "{}_{}".format(fld, fld_num)
                    if fld_name not in fields:
                        logger.debug("Field {} removed, setting as None".format(fld_name))
                        fields[fld_name] = None

            single_fields = ["mobile_phone", "home_phone"]
            multi_fields = {}
            multi_fields_to_update = []

            for field in fields:
                if field not in single_fields:
                    full_field_arr = field.rsplit("_", 1)
                    full_field_name = full_field_arr[0]
                    field_num = int(full_field_arr[1])

                    if full_field_name in multi_fields:
                        multi_fields[full_field_name][field_num] = fields[field]
                    else:
                        multi_fields[full_field_name] = {field_num: fields[field]}

                if field in personal_info and personal_info[field] == fields[field]:
                    logger.debug("{}: same ({})".format(field, fields[field]))
                else:
                    logger.debug("{}: new: {} from: {}".format(field,
                                                               fields[field],
                                                               personal_info[field] if field in personal_info else None))
                    if field in single_fields:
                        if len(fields[field]) < 1:
                            logger.debug("Field {} with blank value becomes None".format(field))
                            fields[field] = None

                        try:
                            user.set_ldap_attribute(field, "{}".format(fields[field]))
                        except Exception as e:
                            messages.error(request, "Unable to set field {} with value {}: {}".format(field, fields[field], e))
                            logger.debug("Field {} with value {}: {}".format(field, fields[field], e))
                        else:
                            try:
                                if fields[field] == None or len(fields[field]) < 1:
                                    pass
                                else:
                                    messages.success(request, "Set field {} to {}".format(field, fields[field] if not isinstance(fields[field], list) else ", ".join(fields[field])))
                            except Exception as e:
                                messages.error(request, "Unable to set field {}: {}".format(field, e))
                    else:
                        logger.debug("Need to update {} because {} changed".format(full_field_name, field))
                        multi_fields_to_update.append(full_field_name)

            logger.debug("multi_fields_to_update: {}".format(multi_fields_to_update))
            for full_field in multi_fields_to_update:
                ldap_full_field = "{}s".format(full_field)
                field_vals = list(multi_fields[full_field].values())
                logger.debug(field_vals)
                for v in field_vals:
                    logger.debug("field vals: {} {}".format(v, field_vals))
                    if not v:
                        field_vals.remove(v)
                try:
                    user.set_ldap_attribute(ldap_full_field, field_vals)
                except Exception as e:
                    messages.error(request, "Unable to set field {} with value {}: {}".format(ldap_full_field, field_vals, e))
                    logger.debug("Unable to set field {} with value {}: {}".format(ldap_full_field, field_vals, e))
                else:
                    if len(field_vals) == 0 or (len(field_vals) == 1 and len(field_vals[0]) < 1):
                        pass
                    else:
                        messages.success(request, "Set field {} to {}".format(ldap_full_field, field_vals if not isinstance(field_vals, list) else ", ".join(field_vals)))
    return personal_info_form


def get_preferred_pic(user):
    """Get a user's preferred picture attributes to pass as an initial
       value to a PreferredPictureForm.
    """

    preferred_pic = {
        "preferred_photo": user.preferred_photo
    }

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
            for field in fields:
                if field == "preferred_photo":
                    if preferred_pic[field] == fields[field]:
                        logger.debug("{}: same ({})".format(field, fields[field]))
                    else:
                        logger.debug("{}: new: {} from: {}".format(field,
                                                                   fields[field],
                                                                   preferred_pic[field] if field in preferred_pic else None))
                        try:
                            user.set_ldap_attribute(field, fields[field])
                        except Exception as e:
                            messages.error(request, "Unable to set field {} with value {}: {}".format(field, fields[field], e))
                            logger.debug("Unable to set field {} with value {}: {}".format(field, fields[field], e))
                        else:
                            messages.success(request, "Set field {} to {}".format(field, fields[field] if not isinstance(fields[field], list) else ", ".join(fields[field])))
    return preferred_pic_form


def get_privacy_options(user):
    """Get a user's privacy options to pass as an initial value to
       a PrivacyOptionsForm.
    """

    privacy_options = {}

    for ptype in user.permissions:
        for field in user.permissions[ptype]:
            if ptype == "self":
                privacy_options["{}-{}".format(field, ptype)] = user.permissions[ptype][field]
            else:
                privacy_options[field] = user.permissions[ptype][field]

    for field in user.photo_permissions["self"]:
        if field != "default":  # photo_permissions["default"] is the same as show on import
            privacy_options["photoperm-{}".format(field)] = user.photo_permissions["parent"]
            privacy_options["photoperm-{}-{}".format(field, "self")] = user.photo_permissions["self"][field]

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
                    logger.debug("{}: new: {} from: {}".format(field,
                                                               fields[field],
                                                               privacy_options[field] if field in privacy_options else None))
                    try:
                        user.set_ldap_preference(field, fields[field], request.user.is_eighth_admin)
                    except Exception as e:
                        messages.error(request, "Unable to set field {} with value {}: {}".format(field, fields[field], e))
                        logger.debug("Unable to set field {} with value {}: {}".format(field, fields[field], e))
                    else:
                        messages.success(request, "Set field {} to {}".format(field, fields[field] if not isinstance(fields[field], list) else ", ".join(fields[field])))
    return privacy_options_form


def get_notification_options(user):
    """Get a user's notification options to pass as an initial value to
       a NotificationOptionsForm.
    """

    notification_options = {}
    notification_options["receive_news_emails"] = user.receive_news_emails
    notification_options["receive_eighth_emails"] = user.receive_eighth_emails

    return notification_options


def save_notification_options(request, user):
    notification_options = get_notification_options(user)
    logger.debug(notification_options)
    notification_options_form = NotificationOptionsForm(user, data=request.POST, initial=notification_options)
    if notification_options_form.is_valid():
        logger.debug("Notification options form: valid")
        if notification_options_form.has_changed():
            fields = notification_options_form.cleaned_data
            logger.debug(fields)
            for field in fields:
                if field in notification_options and notification_options[field] == fields[field]:
                    logger.debug("{}: same ({})".format(field, fields[field]))
                else:
                    logger.debug("{}: new: {} from: {}".format(field,
                                                               fields[field],
                                                               notification_options[field] if field in notification_options else None))
                    setattr(user, field, fields[field])
                    user.save()
                    try:
                        messages.success(request, "Set field {} to {}".format(field, fields[field] if not isinstance(fields[field], list) else ", ".join(fields[field])))
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
    """View and process updates to the preferences page.
    """
    user = request.user

    # Clear cache on every pageload
    user.clear_cache()

    ldap_error = None

    if request.method == "POST":

        personal_info_form = save_personal_info(request, user)
        if user.is_student:
            preferred_pic_form = save_preferred_pic(request, user)
        else:
            preferred_pic_form = None
        privacy_options_form = save_privacy_options(request, user)
        notification_options_form = save_notification_options(request, user)

        try:
            save_gcm_options(request, user)
        except AttributeError:
            pass


        if LDAPConnection().did_use_simple_bind():
            ldap_error = True

    else:
        personal_info, num_fields = get_personal_info(user)
        logger.debug(personal_info)
        personal_info_form = PersonalInformationForm(num_fields=num_fields,
                                                     initial=personal_info)

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
        "personal_info_form": personal_info_form,
        "preferred_pic_form": preferred_pic_form,
        "privacy_options_form": privacy_options_form,
        "notification_options_form": notification_options_form,
        "ldap_error": ldap_error
    }
    return render(request, "preferences/preferences.html", context)


@login_required
def privacy_options_view(request):
    """View and edit privacy options for a user.
    """
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

    context = {
        "privacy_options_form": privacy_options_form,
        "profile_user": user
    }
    return render(request, "preferences/privacy_options.html", context)


@login_required
def ldap_test(request):
    from intranet.db.ldap_db import LDAPConnection
    from intranet import settings

    c = LDAPConnection()

    results = ""

    search_dn = request.POST.get("search_dn")
    search_q = request.POST.get("search_q")
    search_attrs = request.POST.getlist("search_attrs")

    user_attribute_dn = request.POST.get("user_attribute_dn")
    user_attribute_attrs = request.POST.getlist("user_attribute_attrs")
    if request.method == "POST":
        if "search_q" in request.POST:
            try:
                req = c.search(search_dn, search_q, search_attrs)
            except Exception as e:
                results += "EXCEPTION: {}\n".format(e)
            else:
                logger.debug(req)
                if not isinstance(req, list):
                    req = [req]
                for row in req:
                    results += "{}: \n".format(row[0])
                    for perm, value in row[1].items():
                        results += "\t{}: {}\n".format(perm, value)

        if "user_attribute_dn" in request.POST:
            if "dc=edu" not in user_attribute_dn:
                user_attribute_dn = User.objects.get(id=user_attribute_dn).dn
            try:
                req = c.user_attributes(user_attribute_dn, user_attribute_attrs)
            except Exception as e:
                results += "EXCEPTION: {}\n".format(e)
            else:
                logger.debug(req)
                result = req.first_result()
                logger.debug(result)
                if isinstance(result, dict):
                    for perm, value in result.items():
                        logger.debug("{} {}".format(perm, value))
                        results += "{}: {}\n".format(perm, value)
                else:
                    results += "Empty result"

    logger.debug(results)

    context = {
        "search_dn": search_dn or settings.USER_DN or "",
        "search_q": search_q or "",
        "search_attrs": search_attrs or "",
        "user_attribute_dn": user_attribute_dn or "",
        "user_attribute_attrs": user_attribute_attrs or "",
        "results": results
    }

    return render(request, "preferences/ldap.html", context)
