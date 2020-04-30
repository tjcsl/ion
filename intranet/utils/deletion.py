import logging

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.deletion import Collector
from django.utils import timezone

logger = logging.getLogger(__name__)


def set_historical_user(collector, field, sub_objs, using):
    from intranet.apps.eighth.models import EighthSignup, EighthSponsor  # pylint: disable=import-outside-toplevel,cyclic-import

    teststaff, _ = get_user_model().objects.get_or_create(id=7011)
    for obj in sub_objs:
        if isinstance(obj, EighthSignup):
            scheduled_activity = obj.scheduled_activity
            if scheduled_activity.block.date < timezone.localdate():
                if scheduled_activity.archived_member_count:
                    scheduled_activity.archived_member_count += 1
                else:
                    scheduled_activity.archived_member_count = 1
                scheduled_activity.save()
        elif isinstance(obj, EighthSponsor):
            handle_eighth_sponsor_deletion(obj, EighthSponsor)
            sub_objs = sub_objs.exclude(pk=obj.pk)
        else:
            attribute = str(field).rsplit(".")[-1]  # FIXME: Is there a better way to do this?
            setattr(obj, attribute, teststaff)
            obj.save()
            sub_objs = sub_objs.exclude(pk=obj.pk)

    models.CASCADE(collector, field, sub_objs, using)


def handle_eighth_sponsor_deletion(in_obj, eighth_sponsor):
    teststaff, _ = get_user_model().objects.get_or_create(id=7011)
    c = Collector(using="default")
    c.collect([in_obj])
    objects = c.instances_with_model()
    for obj in objects:
        if not isinstance(obj[1], eighth_sponsor):
            obj[1].user = teststaff
            obj[1].save()
        else:
            original = obj[1]
    original.delete()
