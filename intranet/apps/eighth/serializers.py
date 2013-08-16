from .models import EighthBlock, EighthActivity
from rest_framework import serializers


class EighthBlockSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = EighthBlock
        fields = ("id", "date", "block", "locked", "activities")

class EighthActivitySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = EighthActivity
        fields = ("id", "name", "description", "restricted", "presign", "one_a_day", "both_blocks", "sticky", "special")




# class EighthActivity(models.Model):

#     """Represents an eighth period activity.

#     Attributes:
#         - name -- The name of the activity.
#         - sponsors -- The EighthSponsors for the activity.

#     """
#     name = models.CharField(max_length=63)
#     description = models.TextField()
#     sponsors = models.ManyToManyField(EighthSponsor)
#     rooms = models.ManyToManyField(EighthRoom)

#     restricted = models.BooleanField(default=False)
#     presign = models.BooleanField(default=False)
#     one_a_day = models.BooleanField(default=False)
#     both_blocks = models.BooleanField(default=False)
#     sticky = models.BooleanField(default=False)
#     special = models.BooleanField(default=False)

#     # Groups allowed

#     # Single students allowed

#     def __unicode__(self):
#         return self.name
