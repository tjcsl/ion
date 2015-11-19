# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers
from rest_framework.reverse import reverse
from .models import User


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


class SubClassSerializer(serializers.Serializer):
    section_id = serializers.CharField(max_length=500)
    url = serializers.HyperlinkedIdentityField(view_name="api_user_class_detail")
    name = serializers.CharField(max_length=500)


class AddressSerializer(serializers.Serializer):
    street = serializers.CharField(max_length=500)
    city = serializers.CharField(max_length=200)
    state = serializers.CharField(max_length=100)
    postal_code = serializers.CharField(max_length=10)


class StudentSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="api_user_profile_detail")
    first_name = serializers.CharField(max_length=200)
    user_type = serializers.CharField(max_length=100)
    grade = GradeSerializer()

    class Meta:
        model = User
        fields = ('id', 'url', 'user_type', 'full_name', 'first_name', 'grade')


class CounselorTeacherSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="api_user_profile_detail")
    last_name = serializers.CharField(max_length=200)
    user_type = serializers.CharField(max_length=100)

    class Meta:
        model = User
        fields = ('id', 'url', 'user_type', 'full_name', 'last_name')


class HyperlinkedImageField(serializers.HyperlinkedIdentityField):

    def get_url(self, obj, view_name, request, format):
        s = super(HyperlinkedImageField, self).get_url(obj, view_name, request, format)
        if "format=" in s:
            return "{}format=jpg".format(s.split("format=")[0])
        return s


class UserSerializer(serializers.ModelSerializer):
    grade = GradeSerializer()
    classes = SubClassSerializer(many=True)
    address = AddressSerializer()
    counselor = CounselorTeacherSerializer()
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
    picture = HyperlinkedImageField(view_name="api_user_profile_picture_default", format="jpg")

    class Meta:
        model = User
        fields = ('id', 'ion_username', 'sex', 'title', 'display_name', 'full_name', 'short_name', 'first_name', 'middle_name', 'last_name', 'common_name', 'nickname', 'tj_email', 'emails', 'grade', 'graduation_year', 'birthday', 'user_type', 'home_phone', 'mobile_phone', 'other_phones', 'webpages', 'counselor', 'address', 'picture', 'is_eighth_admin', 'is_announcements_admin', 'is_teacher', 'is_student', 'classes')


class ClassSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=300)
    class_id = serializers.CharField(max_length=20)
    room_number = serializers.CharField(max_length=100)
    course_length = serializers.IntegerField()
    periods = serializers.ListField(
        child=serializers.IntegerField()
    )
    quarters = serializers.ListField(
        child=serializers.IntegerField()
    )
    teacher = CounselorTeacherSerializer()
    students = StudentSerializer(many=True)
