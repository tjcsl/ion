from django.shortcuts import render
from .forms import (
    PersonalInformationForm, PreferredPictureForm, PrivacyOptionsForm
)


def preferences_view(request):
    personal_info_form = PersonalInformationForm(num_phones=2,
                                                 num_emails=3,
                                                 num_webpages=4)

    preferred_pic_form = PreferredPictureForm(request.user)
    privacy_options_form = PrivacyOptionsForm(request.user)

    context = {
        "personal_info_form": personal_info_form,
        "preferred_pic_form": preferred_pic_form
    }
    return render(request, "preferences/preferences.html", context)
