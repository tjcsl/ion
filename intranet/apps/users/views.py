import os
from cStringIO import StringIO
import logging
import io
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import render
from .models import User, Grade
from intranet import settings

logger = logging.getLogger(__name__)


@login_required
def profile_view(request, user_id=None):
    if user_id is not None:
        profile_user = User.objects.create_user(id=user_id)
        if profile_user is None:
            raise Http404
    else:
        profile_user = request.user

    return render(request, 'users/profile.html', {'user': request.user,
                                                  'profile_user': profile_user})


@login_required
def picture_view(request, user_id, year=None):
    user = User.objects.create_user(id=user_id)
    default_image_path = os.path.join(settings.PROJECT_ROOT, "static/img/pig.jpg")

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
                    data = user.photo_binary(Grade.names[i - 9])
                    if data:
                        break
                if data is None:
                    image_buffer = io.open(default_image_path, mode="rb")
                else:
                    image_buffer = StringIO(data)

            # Exclude 'graduate' from names array
            elif preferred in Grade.names[:-1]:
                data = user.photo_binary(preferred)

                if data:
                    image_buffer = StringIO(data)
                else:
                    image_buffer = io.open(default_image_path)
            else:
                image_buffer = io.open(default_image_path, mode="rb")
        else:
            data = user.photo_binary(year)
            if data:
                image_buffer = StringIO(data)
            else:
                image_buffer = io.open(default_image_path, mode="rb")

        response = HttpResponse(mimetype="image/jpeg")
        response["Content-Disposition"] = "filename={}_{}.jpg".format(user_id,
                                          (year or preferred))
        img = image_buffer.read()
        image_buffer.close()
        response.write(img)

        return response