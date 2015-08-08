from django.shortcuts import render
from .forms import (
    PersonalInformationForm, PreferredPictureForm, PrivacyOptionsForm
)


def preferences_view(request):
    user = request.user

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

    personal_info_form = PersonalInformationForm(num_phones=num_phones,
                                                 num_emails=num_emails,
                                                 num_webpages=num_webpages,
                                                 initial=personal_info)

    preferred_pic_form = PreferredPictureForm(user)
    privacy_options_form = PrivacyOptionsForm(user)

    context = {
        "personal_info_form": personal_info_form,
        "preferred_pic_form": preferred_pic_form,
        "privacy_options_form": privacy_options_form
    }
    return render(request, "preferences/preferences.html", context)
