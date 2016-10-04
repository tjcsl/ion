# -*- coding: utf-8 -*-
import logging

from django.db import models

from intranet.apps.users.models import User

logger = logging.getLogger(__name__)


def SET_HISTORICAL_USER(collector, field, sub_objs, using):
    teststaff = User.get_user(id=7011)
    updated = []
    for obj in sub_objs:
        attribute = str(field).rsplit('.')[-1]  # FIXME: Is there a better way to do this?
        setattr(obj, attribute, teststaff)
        try:
            obj.save()
            updated.append(obj)
            sub_objs = sub_objs.exclude(pk=obj.pk)
        except:
            continue
    models.CASCADE(collector, field, sub_objs, using)
    return
