from .models import EighthBlock
from rest_framework import serializers


class EighthBlockSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = EighthBlock
        fields = ("id", "date", "block", "locked")
