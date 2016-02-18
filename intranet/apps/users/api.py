# -*- coding: utf-8 -*-

import io
import os

from django.conf import settings

from intranet.apps.search.views import get_search_results

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Class, Grade, User
from .renderers import JPEGRenderer
from .serializers import (ClassSerializer, CounselorTeacherSerializer,
                          StudentSerializer, UserSerializer)


class ProfileDetail(generics.RetrieveAPIView):
    """API endpoint that retrieves an Ion profile.

    /api/profile: retrieve your profile
    /api/profile/<pk>: retrieve the profile of the user with id <pk>

    """
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def retrieve(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            user = User.objects.get(pk=kwargs['pk'])
        else:
            user = request.user

        serializer = self.get_serializer(user)
        data = serializer.data
        return Response(data)


class ProfilePictureDetail(generics.RetrieveAPIView):
    """API endpoint that retrieves an Ion profile picture.

    /api/profile/<pk>/picture: retrieve default profile picture
    /api/profile/<pk>/picture/<photo_year>: retrieve profile picture for year <photo_year>

    """
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JPEGRenderer,)

    def retrieve(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            user = User.objects.get(pk=kwargs['pk'])
        else:
            user = request.user

        binary = None
        if 'photo_year' in kwargs:
            photo_year = kwargs['photo_year']
            if photo_year in Grade.names:
                binary = user.photo_binary(photo_year)
        else:
            binary = user.default_photo()
        if not binary:
            default_image_path = os.path.join(settings.PROJECT_ROOT, "static/img/default_profile_pic.png")
            binary = io.open(default_image_path, mode="rb").read()

        response = Response(binary, content_type='image/jpeg')
        return response


class ClassDetail(generics.RetrieveAPIView):
    """API endpoint that retrieves details of a TJHSST class."""
    serializer_class = ClassSerializer
    permission_classes = (IsAuthenticated,)

    def retrieve(self, request, *args, **kwargs):
        cl = Class(id=kwargs['pk'])

        serializer = self.get_serializer(cl)
        return Response(serializer.data)


class Search(generics.RetrieveAPIView):
    """API endpoint that retrieves the results of a search for Ion users.

    Paginated using ?page=<page>

    """

    permission_classes = (IsAuthenticated,)
    queryset = User.objects.all()

    def retrieve(self, request, *args, **kwargs):
        query = kwargs['query']
        user_ids = []
        query = query.replace("+", " ")
        query_error, results = get_search_results(query)
        for unserialized_user in results:
            user_ids.append(unserialized_user.id)

        queryset = User.objects.filter(pk__in=user_ids)
        users = self.paginate_queryset(queryset)

        response = []
        for user in users:
            if user.is_student:
                response.append(StudentSerializer(user, context={'request': request}).data)
            else:
                response.append(CounselorTeacherSerializer(user, context={'request': request}).data)

        return self.get_paginated_response(response)
