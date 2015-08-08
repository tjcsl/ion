# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import messages
from django.shortcuts import render
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

def get_preferred_pic(user):
    """Get a user's preferred picture attributes to pass as an initial
       value to a PreferredPictureForm.
    """

    preferred_pic = {
        "preferred_photo": user.preferred_photo
    }

    return preferred_pic

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
        if field != "default": # photo_permissions["default"] is the same as show on import
            privacy_options["photoperm-{}".format(field)] = user.photo_permissions["parent"]
            privacy_options["photoperm-{}-{}".format(field, "self")] = user.photo_permissions["self"][field]

    return privacy_options

def get_notification_options(user):
    """Get a user's notification options to pass as an initial value to
       a NotificationOptionsForm.
    """

    notification_options = {}
    notification_options["receive_news_emails"] = user.receive_news_emails
    notification_options["receive_eighth_emails"] = user.receive_eighth_emails

    return notification_options

def preferences_view(request):
    """View and process updates to the preferences page.
    """
    user = request.user

    # Clear cache on every pageload
    user.clear_cache()

    if request.method == "POST":
        personal_info, num_fields = get_personal_info(user)
        personal_info_form = PersonalInformationForm(num_fields=num_fields, data=request.POST, initial=personal_info)
        logger.debug(personal_info_form)
        if personal_info_form.is_valid():
            logger.debug("Personal info: valid")
            if personal_info_form.has_changed():
                fields = personal_info_form.cleaned_data
                logger.debug(fields)
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
                                messages.error(request, "Field {} with value {}: {}".format(field, fields[field], e))
                                logger.debug("Field {} with value {}: {}".format(field, fields[field], e))
                            else:
                                messages.success(request, "Set field {} to {}".format(field, fields[field]))
                        else:
                            logger.debug("Need to update {} because {} changed".format(full_field_name, field))
                            multi_fields_to_update.append(full_field_name)

                logger.debug(multi_fields_to_update)
                for full_field in multi_fields_to_update:
                    ldap_full_field = "{}s".format(full_field)
                    field_vals = multi_fields[full_field].values()
                    for v in field_vals:
                        if not v:
                            field_vals.remove(v)

                    try:
                        user.set_ldap_attribute(ldap_full_field, field_vals)
                    except Exception as e:
                        messages.error(request, "Field {} with value {}: {}".format(ldap_full_field, field_vals, e))
                        logger.debug("Field {} with value {}: {}".format(ldap_full_field, field_vals, e))
                    else:
                        messages.success(request, "Set field {} to {}".format(ldap_full_field, field_vals))

                logger.debug("Complete.")


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
                                messages.error(request, "Field {} with value {}: {}".format(field, fields[field], e))
                                logger.debug("Field {} with value {}: {}".format(field, fields[field], e))
                            else:
                                messages.success(request, "Set field {} to {}".format(field, fields[field]))

        privacy_options = get_privacy_options(user)
        logger.debug(privacy_options)
        privacy_options_form = PrivacyOptionsForm(user, data=request.POST, initial=privacy_options)


        notification_options = get_notification_options(user)
        logger.debug(notification_options)
        notification_options_form = NotificationOptionsForm(user, data=request.POST, initial=notification_options)

    else:
        personal_info, num_fields = get_personal_info(user)
        logger.debug(personal_info)
        personal_info_form = PersonalInformationForm(num_fields=num_fields,
                                                     initial=personal_info)

        preferred_pic = get_preferred_pic(user)
        logger.debug(preferred_pic)
        preferred_pic_form = PreferredPictureForm(user, initial=preferred_pic)

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
        "notification_options_form": notification_options_form
    }
    return render(request, "preferences/preferences.html", context)
