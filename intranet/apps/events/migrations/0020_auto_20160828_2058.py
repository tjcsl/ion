# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-08-29 00:58
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [('events', '0019_tjstaruuidmap'),]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='approved_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_event',
                                    to=settings.AUTH_USER_MODEL),),
        migrations.AlterField(
            model_name='event',
            name='rejected_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='rejected_event',
                                    to=settings.AUTH_USER_MODEL),),
        migrations.AlterField(
            model_name='event',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),),
    ]
