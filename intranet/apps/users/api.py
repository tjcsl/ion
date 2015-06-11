# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import generics
from rest_framework.response import Response
from intranet.apps.search.views import get_search_results
from .models import User, Class
from .serializers import UserSerializer, ClassSerializer, StudentSerializer, CounselorTeacherSerializer

class ProfileDetail(generics.RetrieveAPIView):
    """API endpoint that retrieves an Ion profile

    /api/profile: retrieve your profile
    /api/profile/<pk>: retrieve the profile of the user with id <pk>
    """
    serializer_class = UserSerializer

    def retrieve(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            user = User.objects.get(pk=kwargs['pk'])
        else:
            user = request.user

        serializer = self.get_serializer(user)
        return Response(serializer.data)

class ClassDetail(generics.RetrieveAPIView):
    """API endpoint that retrieves details of a TJHSST class
    """
    serializer_class = ClassSerializer
    
    def retrieve(self, request, *args, **kwargs):
        cl = Class(id=kwargs['pk'])

        serializer = self.get_serializer(cl)
        return Response(serializer.data)

class Search(generics.RetrieveAPIView):
    """API endpoint that retrieves the results of a search for Ion users

    Paginated using ?page=<page>
    """

    def retrieve(self, request, *args, **kwargs):
        query = kwargs['query']
        user_ids = []

        query_error, results = get_search_results(query)
        for unserialized_user in results['hits']['hits']:
            user_ids.append(unserialized_user['_source']['ion_id'])

        queryset = User.objects.filter(pk__in=user_ids)
        users = self.paginate_queryset(queryset)

        response = []
        for user in users:
            if user.is_student:
                response.append(StudentSerializer(user, context={'request': request}).data)
            else:
                response.append(CounselorTeacherSerializer(user, context={'request': request}).data)

        return self.get_paginated_response(response)
