from rest_framework import serializers
from .models import EighthBlock, EighthActivity
# from intranet.apps.users.serializers import UserSerializer


class EighthActivitySerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = EighthActivity
        fields = ("id",
                  "url",
                  "name",
                  "description",
                  "restricted",
                  "presign",
                  "one_a_day",
                  "both_blocks",
                  "sticky",
                  "special")


class EighthBlockListSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = EighthBlock
        # Omit activities so people can't kill the database
        fields = ("id",
                  "url",
                  "date",
                  "block",
                  "locked")


class FoobarField(serializers.Field):
    def to_native(self, obj):
        return "foobar"

class EighthBlockDetailSerializer(serializers.Serializer):
    # activities = EighthActivitySerializer()
    foo = FoobarField(source='*')
    class Meta:
        # model = EighthBlock
        fields = ("foo",)


# class EighthSponsorSerializer(models.Model):
#   pass
