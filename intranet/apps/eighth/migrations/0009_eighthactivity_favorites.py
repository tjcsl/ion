# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('eighth', '0008_auto_20150318_1305'),
    ]

    operations = [
        migrations.AddField(
            model_name='eighthactivity',
            name='favorites',
            field=models.ManyToManyField(related_name='favorited_activity_set', to=settings.AUTH_USER_MODEL, blank=True),
        ),
    ]
