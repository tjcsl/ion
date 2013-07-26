import os
from cStringIO import StringIO
from PIL import Image
import logging
import ldap
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import render
from .models import User, Grade
from intranet import settings

logger = logging.getLogger(__name__)


@login_required
def profile(request, user_id=None):
    if user_id is not None:
        profile_user = User.create(id=user_id)
        if profile_user is None:
            raise Http404
    else:
        profile_user = request.user

    return render(request, 'users/profile.html', {'user': profile_user})


@login_required
def picture(request, user_id, year=None):
    user = User.create(id=user_id)
    default_image_path = os.path.join(settings.PROJECT_ROOT,
                                      "static/img/pig.jpg")
    if user is None:
        raise Http404
    else:
        if year is None:
            preferred = user.preferred_photo
            if preferred is not None:
                if preferred.endswith("Photo"):
                    preferred = preferred[:-len("Photo")]

            if preferred == "AUTO":
                if user.user_type == "tjhsstTeacher":
                    current_grade = 12
                else:
                    current_grade = int(user.grade)
                    if current_grade == 13:
                        current_grade = 12

                for i in reversed(range(9, current_grade + 1)):
                    data = user.picture_base64(Grade.names[i - 9])
                    if data:
                        break
                if not data:
                    print "hi"
                    image_file = default_image_path
                else:
                    image_file = StringIO(data)
            # Exclude 'graduate' from names array
            elif preferred in Grade.names[:-1]:
                data = user.picture_base64(preferred)
                image_file = StringIO(data)
            else:
                image_file = default_image_path
        else:
            data = user.picture_base64(year)
            if data:
                image_file = StringIO(data)
            else:
                image_file = default_image_path

        image = Image.open(image_file)
        response = HttpResponse(mimetype='image/jpeg')
        image.save(response, "JPEG")
        return response
