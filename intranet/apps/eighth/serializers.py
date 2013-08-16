from rest_framework import serializers
from .models import EighthBlock, EighthActivity
from intranet.apps.users.serializers import UserSerializer

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

class EighthBlockDetailSerializer(serializers.HyperlinkedModelSerializer):
    activities = EighthActivitySerializer()
    class Meta:
        model = EighthBlock
        fields = ("id",
                  "url",
                  "date",
                  "block",
                  "locked",
                  "activities")

class EighthSponsorSerializer(models.Model):




# class EighthActivity(models.Model):

#     """Represents an eighth period activity.

#     Attributes:
#         - name -- The name of the activity.
#         - sponsors -- The EighthSponsors for the activity.

#     """
#     sponsors = models.ManyToManyField(EighthSponsor)
#     rooms = models.ManyToManyField(EighthRoom)

#
#     # Groups allowed

#     # Single students allowed

#     def __unicode__(self):
#         return self.name
