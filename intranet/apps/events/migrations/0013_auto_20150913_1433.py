# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('events', '0012_auto_20150913_1433'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='rejected_by',
            field=models.ForeignKey(related_name='rejected_event', to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='approved_by',
            field=models.ForeignKey(related_name='approved_event', to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
