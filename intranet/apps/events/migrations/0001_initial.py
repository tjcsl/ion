# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('eighth', '0008_auto_20150318_1305'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('announcements', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=100)),
                ('description', models.TextField(max_length=10000, blank=True)),
                ('start', models.DateTimeField()),
                ('end', models.DateTimeField()),
                ('created_date', models.DateTimeField(auto_now=True)),
                ('announcement', models.ForeignKey(blank=True, to='announcements.Announcement', null=True)),
                ('creator', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('eighth_activity', models.ForeignKey(blank=True, to='eighth.EighthActivity', null=True)),
                ('eighth_scheduled_activity', models.ForeignKey(blank=True, to='eighth.EighthScheduledActivity', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
