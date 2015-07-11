# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('events', '0007_auto_20150628_1227'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='attending',
            field=models.ManyToManyField(related_name='attending', to=settings.AUTH_USER_MODEL, blank=True),
        ),
    ]
