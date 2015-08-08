from django.shortcuts import render
from .forms import (
    PersonalInformationForm, PreferredPictureForm, PrivacyOptionsForm
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

    return personal_info

def get_preferred_pic(user):
    """Get a user's preferred picture attributes to pass as an initial
       value to a PreferredPictureForm.
    """

    preferred_pic = {
        "preferred_photo": user.preferred_photo
    }

    return get_preferred_pic

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

def preferences_view(request):
    user = request.user

    personal_info = get_personal_info(user)
    logger.debug(personal_info)
    personal_info_form = PersonalInformationForm(num_phones=num_phones,
                                                 num_emails=num_emails,
                                                 num_webpages=num_webpages,
                                                 initial=personal_info)

    perferred_pic = get_preferred_pic(user)
    logger.debug(preferred_pic)
    preferred_pic_form = PreferredPictureForm(user, initial=preferred_pic)

    privacy_options = get_privacy_options(user)
    logger.debug(privacy_options)
    privacy_options_form = PrivacyOptionsForm(user, initial=privacy_options)

    context = {
        "personal_info_form": personal_info_form,
        "preferred_pic_form": preferred_pic_form,
        "privacy_options_form": privacy_options_form
    }
    return render(request, "preferences/preferences.html", context)
