# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import generics
from rest_framework.response import Response
from .models import User, Class
from .serializers import UserSerializer, ClassSerializer

class ProfileDetail(generics.RetrieveAPIView):
    """API endpoint that retrieves an Ion profile
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
    serializer_class = ClassSerializer
    
    def retrieve(self, request, *args, **kwargs):
        cl = Class(id=kwargs['pk'])

        serializer = self.get_serializer(cl)
        return Response(serializer.data)

