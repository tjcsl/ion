from .models import EighthBlock, EighthActivity
from rest_framework import serializers


class EighthBlockDetailSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = EighthBlock
        fields = ("id",
                  "url",
                  "date",
                  "block",
                  "locked",
                  "activities")

class EighthBlockListSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = EighthBlock
        # Omitting "activities" so people can't kill the database
        fields = ("id",
                  "url",
                  "date",
                  "block",
                  "locked")

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
