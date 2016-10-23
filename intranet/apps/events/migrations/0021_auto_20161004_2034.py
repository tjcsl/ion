# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-05 00:34
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import intranet.utils.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0020_auto_20160828_2058'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='approved_by',
            field=models.ForeignKey(null=True, on_delete=intranet.utils.deletion.set_historical_user,
                                    related_name='approved_event', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='event',
            name='rejected_by',
            field=models.ForeignKey(null=True, on_delete=intranet.utils.deletion.set_historical_user,
                                    related_name='rejected_event', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='event',
            name='user',
            field=models.ForeignKey(null=True, on_delete=intranet.utils.deletion.set_historical_user, to=settings.AUTH_USER_MODEL),
        ),
    ]
