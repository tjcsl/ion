from rest_framework import serializers


class UserListSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=63)
    short_name = serializers.CharField(max_length=31)
    # display_name = serializers.
    ion_id = serializers.IntegerField()
    ion_username = serializers.CharField(max_length=15)

    email = serializers.EmailField()
    content = serializers.CharField(max_length=200)
    created = serializers.DateTimeField()
