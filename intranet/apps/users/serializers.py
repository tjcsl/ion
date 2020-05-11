# pylint: disable=abstract-method
from rest_framework import serializers

from django.contrib.auth import get_user_model

from .models import Address


class GradeSerializer(serializers.Serializer):
    number = serializers.IntegerField()
    name = serializers.CharField(max_length=20)


class AddressSerializer(serializers.ModelSerializer):
    street = serializers.CharField(max_length=500)
    city = serializers.CharField(max_length=200)
    state = serializers.CharField(max_length=100)
    postal_code = serializers.CharField(max_length=10)

    class Meta:
        model = Address
        fields = ("street", "city", "state", "postal_code")


class StudentSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="api_user_profile_detail")
    first_name = serializers.CharField(max_length=200)
    last_name = serializers.CharField(max_length=200)
    user_type = serializers.CharField(max_length=100)
    username = serializers.CharField(max_length=100)
    grade = GradeSerializer()

    class Meta:
        model = get_user_model()
        fields = ("id", "url", "user_type", "username", "full_name", "first_name", "last_name", "grade")


class CounselorTeacherSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="api_user_profile_detail")
    first_name = serializers.CharField(max_length=200)
    last_name = serializers.CharField(max_length=200)
    user_type = serializers.CharField(max_length=100)
    username = serializers.CharField(max_length=100)

    class Meta:
        model = get_user_model()
        fields = ("id", "url", "user_type", "username", "full_name", "first_name", "last_name")


class HyperlinkedImageField(serializers.HyperlinkedIdentityField):
    def get_url(self, obj, view_name, request, format):  # pylint: disable=redefined-builtin
        s = super(HyperlinkedImageField, self).get_url(obj, view_name, request, format)
        if "format=" in s:
            return "{}format=jpg".format(s.split("format=", 1)[0])
        return s


class UserSerializer(serializers.ModelSerializer):
    grade = GradeSerializer()
    address = AddressSerializer()
    counselor = CounselorTeacherSerializer()
    ion_username = serializers.CharField(max_length=500)
    display_name = serializers.CharField(max_length=400)
    nickname = serializers.CharField(max_length=200)
    title = serializers.CharField(max_length=200)
    first_name = serializers.CharField(max_length=200)
    middle_name = serializers.CharField(max_length=200)
    last_name = serializers.CharField(max_length=200)
    sex = serializers.CharField(max_length=10)
    user_type = serializers.CharField(max_length=100)
    graduation_year = serializers.IntegerField()
    tj_email = serializers.StringRelatedField()
    emails = serializers.StringRelatedField(many=True)
    phones = serializers.StringRelatedField(many=True)
    websites = serializers.StringRelatedField(many=True)
    picture = HyperlinkedImageField(view_name="api_user_profile_picture_default", format="jpg")

    absences = serializers.IntegerField(source="absence_count")

    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "ion_username",
            "sex",
            "title",
            "display_name",
            "full_name",
            "short_name",
            "first_name",
            "middle_name",
            "last_name",
            "nickname",
            "tj_email",
            "emails",
            "grade",
            "graduation_year",
            "user_type",
            "phones",
            "websites",
            "counselor",
            "address",
            "picture",
            "is_eighth_admin",
            "is_announcements_admin",
            "is_teacher",
            "is_student",
            "absences",
        )
