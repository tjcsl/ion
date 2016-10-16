# -*- coding: utf-8 -*-
import logging
from datetime import date

from django.db import models
from django.db.models.deletion import Collector

from intranet.apps.users.models import User

logger = logging.getLogger(__name__)


def set_historical_user(collector, field, sub_objs, using):
    from intranet.apps.eighth.models import EighthSignup, EighthSponsor
    teststaff = User.get_user(id=7011)
    for obj in sub_objs:
        if isinstance(obj, EighthSignup):
            scheduled_activity = obj.scheduled_activity
            if scheduled_activity.block.date < date.today():
                if scheduled_activity.archived_member_count:
                    scheduled_activity.archived_member_count += 1
                else:
                    scheduled_activity.archived_member_count = 1
                scheduled_activity.save()
        elif isinstance(obj, EighthSponsor):
            handle_eighth_sponsor_deletion(obj, EighthSponsor)
            sub_objs = sub_objs.exclude(pk=obj.pk)
        else:
            attribute = str(field).rsplit('.')[-1]  # FIXME: Is there a better way to do this?
            setattr(obj, attribute, teststaff)
            obj.save()
            sub_objs = sub_objs.exclude(pk=obj.pk)

    models.CASCADE(collector, field, sub_objs, using)


def handle_eighth_sponsor_deletion(in_obj, eighth_sponsor):
    teststaff = User.get_user(id=7011)
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
