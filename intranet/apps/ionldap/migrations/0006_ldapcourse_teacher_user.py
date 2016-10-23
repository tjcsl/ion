# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-31 00:21
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ionldap', '0005_auto_20160225_1924'),
    ]

    operations = [
        migrations.AddField(
            model_name='ldapcourse',
            name='teacher_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ionldap_course_teacher',
                                    to=settings.AUTH_USER_MODEL),),
    ]
