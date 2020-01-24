import io
import os

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.conf import settings
from django.contrib.auth import get_user_model

from intranet.apps.search.views import get_search_results

from ..auth.rest_permissions import DenyRestrictedPermission
from .models import Grade
from .renderers import JPEGRenderer
from .serializers import CounselorTeacherSerializer, StudentSerializer, UserSerializer


class ProfileDetail(generics.RetrieveAPIView):
    """API endpoint that retrieves an Ion profile.

    /api/profile: retrieve your profile
    /api/profile/<pk>: retrieve the profile of the user with id <pk>
    /api/profile/<username>: retrieve the profile of the user with username <username>

    """

    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def retrieve(self, request, *args, **kwargs):
        if "pk" in kwargs:
            user = get_user_model().objects.get(pk=kwargs["pk"])
        elif "username" in kwargs:
            user = get_user_model().objects.get(username__iexact=kwargs["username"])
        else:
            user = request.user

        if request.user.is_restricted and user != request.user:
            raise get_user_model().DoesNotExist

        return Response(self.get_serializer(user).data)


class ProfilePictureDetail(generics.RetrieveAPIView):
    """API endpoint that retrieves an Ion profile picture.

    /api/profile/<pk>/picture: retrieve default profile picture
    /api/profile/<pk>/picture/<photo_year>: retrieve profile picture for year <photo_year>

    """

    serializer_class = UserSerializer
    permission_classes = (DenyRestrictedPermission,)
    renderer_classes = (JPEGRenderer,)

    def retrieve(self, request, *args, **kwargs):
        if "pk" in kwargs:
            user = get_user_model().objects.get(pk=kwargs["pk"])
        elif "username" in kwargs:
            user = get_user_model().objects.get(username=kwargs["username"])
        else:
            user = request.user

        binary = None
        if "photo_year" in kwargs:
            photo_year = kwargs["photo_year"]
            if photo_year in Grade.names:
                grade_number = Grade.number_from_name(photo_year)
                if user.photos.filter(grade_number=grade_number).exists():
                    binary = user.photos.filter(grade_number=grade_number).first().binary
                else:
                    binary = None
        else:
            binary = user.default_photo
        if binary is None:
            default_image_path = os.path.join(settings.PROJECT_ROOT, "static/img/default_profile_pic.png")
            binary = io.open(default_image_path, mode="rb").read()

        return Response(binary, content_type="image/jpeg")


class Search(generics.RetrieveAPIView):
    """API endpoint that retrieves the results of a search for Ion users.

    Paginated using ?page=<page>

    """

    permission_classes = (DenyRestrictedPermission,)
    queryset = get_user_model().objects.all()

    def retrieve(self, request, *args, **kwargs):
        query = kwargs["query"]
        user_ids = []
        query = query.replace("+", " ")
        _, results = get_search_results(query)
        for unserialized_user in results:
            user_ids.append(unserialized_user.id)

        queryset = get_user_model().objects.filter(pk__in=user_ids).order_by("pk")
        users = self.paginate_queryset(queryset)

        response = []
        for user in users:
            if user.is_student:
                response.append(StudentSerializer(user, context={"request": request}).data)
            else:
                response.append(CounselorTeacherSerializer(user, context={"request": request}).data)

        return self.get_paginated_response(response)
