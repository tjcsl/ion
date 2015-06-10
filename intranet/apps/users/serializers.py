# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers
from .models import User, Grade, Class, Address

class UserListSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=63)
    short_name = serializers.CharField(max_length=31)
    # display_name = serializers.
    ion_id = serializers.IntegerField()
    ion_username = serializers.CharField(max_length=15)

    email = serializers.EmailField()
    content = serializers.CharField(max_length=200)
    created = serializers.DateTimeField()

class GradeSerializer(serializers.Serializer):
    number = serializers.IntegerField()
    name = serializers.CharField(max_length=20)

class SubUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id')

class ClassSerializer(serializers.Serializer):
    section_id = serializers.CharField(max_length=500)

class AddressSerializer(serializers.Serializer):
    street = serializers.CharField(max_length=500)
    city = serializers.CharField(max_length=200)
    state = serializers.CharField(max_length=100)
    postal_code = serializers.CharField(max_length=10)

class CounselorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'full_name', 'short_name')


class UserSerializer(serializers.ModelSerializer):
    grade = GradeSerializer()
    classes = ClassSerializer(many=True) 
    address = AddressSerializer()
    counselor = CounselorSerializer()
    ion_username = serializers.CharField(max_length=500)
    common_name = serializers.CharField(max_length=200)
    display_name = serializers.CharField(max_length=400)
    nickname = serializers.CharField(max_length=200)
    title = serializers.CharField(max_length=200)
    first_name = serializers.CharField(max_length=200)
    middle_name = serializers.CharField(max_length=200)
    last_name = serializers.CharField(max_length=200)
    sex = serializers.CharField(max_length=10)
    user_type = serializers.CharField(max_length=100)
    graduation_year = serializers.IntegerField()
    emails = serializers.ListField(
            child=serializers.CharField(max_length=500)
            )
    home_phone = serializers.CharField(max_length=50)
    mobile_phone = serializers.CharField(max_length=50)
    other_phones = serializers.ListField(
            child=serializers.CharField(max_length=50)
            )
    webpages = serializers.ListField(
            child=serializers.CharField(max_length=300)
            )
    
    class Meta:
        model = User
        fields = ('id', 'ion_username', 'sex', 'title', 'display_name', 'full_name', 'short_name', 'first_name', 'middle_name', 'last_name', 'common_name', 'nickname', 'tj_email', 'emails', 'grade', 'graduation_year', 'user_type', 'home_phone', 'mobile_phone', 'other_phones', 'webpages', 'counselor', 'address', 'birthday', 'is_eighth_admin', 'is_announcements_admin', 'is_teacher', 'is_student', 'is_staff', 'classes')#, 'ion_id', 'ion_username', 'common_name', 'display_name', 'nickname', 'title', 'first_name', 'middle_name', 'last_name', 'sex', 'user_type', 'graduation_year', 'preferred_photo', 'emails', 'home_phone', 'mobile_phone', 'other_phones', 'webpages', 'startpage')
