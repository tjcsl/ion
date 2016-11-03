# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('eighth', '0027_eighthblock_comments'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalEighthActivity',
            fields=[
                ('id', models.IntegerField(verbose_name='ID', db_index=True, auto_created=True, blank=True)),
                ('created_time', models.DateTimeField(null=True, editable=False, blank=True)),
                ('last_modified_time', models.DateTimeField(null=True, editable=False, blank=True)),
                ('aid', models.CharField(max_length=10, blank=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=2000, blank=True)),
                ('presign', models.BooleanField(default=False)),
                ('one_a_day', models.BooleanField(default=False)),
                ('both_blocks', models.BooleanField(default=False)),
                ('sticky', models.BooleanField(default=False)),
                ('special', models.BooleanField(default=False)),
                ('administrative', models.BooleanField(default=False)),
                ('restricted', models.BooleanField(default=False)),
                ('freshmen_allowed', models.BooleanField(default=False)),
                ('sophomores_allowed', models.BooleanField(default=False)),
                ('juniors_allowed', models.BooleanField(default=False)),
                ('seniors_allowed', models.BooleanField(default=False)),
                ('deleted', models.BooleanField(default=False)),
                ('history_id', models.AutoField(serialize=False, primary_key=True)),
                ('history_date', models.DateTimeField()),
                ('history_type', models.CharField(max_length=1, choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')])),
                ('history_user', models.ForeignKey(related_name='+', on_delete=models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
                'verbose_name': 'historical eighth activity',
            },
        ),
        migrations.CreateModel(
            name='HistoricalEighthBlock',
            fields=[
                ('id', models.IntegerField(verbose_name='ID', db_index=True, auto_created=True, blank=True)),
                ('created_time', models.DateTimeField(null=True, editable=False, blank=True)),
                ('last_modified_time', models.DateTimeField(null=True, editable=False, blank=True)),
                ('date', models.DateField()),
                ('signup_time', models.TimeField(default=datetime.time(12, 30))),
                ('block_letter', models.CharField(max_length=10)),
                ('locked', models.BooleanField(default=False)),
                ('comments', models.CharField(max_length=100, blank=True)),
                ('history_id', models.AutoField(serialize=False, primary_key=True)),
                ('history_date', models.DateTimeField()),
                ('history_type', models.CharField(max_length=1, choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')])),
                ('history_user', models.ForeignKey(related_name='+', on_delete=models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
                'verbose_name': 'historical eighth block',
            },
        ),
        migrations.CreateModel(
            name='HistoricalEighthRoom',
            fields=[
                ('id', models.IntegerField(verbose_name='ID', db_index=True, auto_created=True, blank=True)),
                ('created_time', models.DateTimeField(null=True, editable=False, blank=True)),
                ('last_modified_time', models.DateTimeField(null=True, editable=False, blank=True)),
                ('name', models.CharField(max_length=100)),
                ('capacity', models.SmallIntegerField(default=28)),
                ('history_id', models.AutoField(serialize=False, primary_key=True)),
                ('history_date', models.DateTimeField()),
                ('history_type', models.CharField(max_length=1, choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')])),
                ('history_user', models.ForeignKey(related_name='+', on_delete=models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
                'verbose_name': 'historical eighth room',
            },
        ),
        migrations.CreateModel(
            name='HistoricalEighthScheduledActivity',
            fields=[
                ('id', models.IntegerField(verbose_name='ID', db_index=True, auto_created=True, blank=True)),
                ('created_time', models.DateTimeField(null=True, editable=False, blank=True)),
                ('last_modified_time', models.DateTimeField(null=True, editable=False, blank=True)),
                ('admin_comments', models.CharField(max_length=1000, blank=True)),
                ('title', models.CharField(max_length=1000, blank=True)),
                ('comments', models.CharField(max_length=1000, blank=True)),
                ('capacity', models.SmallIntegerField(null=True, blank=True)),
                ('attendance_taken', models.BooleanField(default=False)),
                ('cancelled', models.BooleanField(default=False)),
                ('history_id', models.AutoField(serialize=False, primary_key=True)),
                ('history_date', models.DateTimeField()),
                ('history_type', models.CharField(max_length=1, choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')])),
                ('activity', models.ForeignKey(related_name='+', on_delete=models.deletion.DO_NOTHING,
                                               db_constraint=False, blank=True, to='eighth.EighthActivity', null=True)),
                ('block', models.ForeignKey(related_name='+', on_delete=models.deletion.DO_NOTHING,
                                            db_constraint=False, blank=True, to='eighth.EighthBlock', null=True)),
                ('history_user', models.ForeignKey(related_name='+', on_delete=models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
                'verbose_name': 'historical eighth scheduled activity',
            },
        ),
        migrations.CreateModel(
            name='HistoricalEighthSignup',
            fields=[
                ('id', models.IntegerField(verbose_name='ID', db_index=True, auto_created=True, blank=True)),
                ('created_time', models.DateTimeField(null=True, editable=False, blank=True)),
                ('last_modified_time', models.DateTimeField(null=True, editable=False, blank=True)),
                ('time', models.DateTimeField(editable=False, blank=True)),
                ('after_deadline', models.BooleanField(default=False)),
                ('previous_activity_name', models.CharField(default=None, max_length=200, null=True, blank=True)),
                ('previous_activity_sponsors', models.CharField(default=None, max_length=10000, null=True, blank=True)),
                ('pass_accepted', models.BooleanField(default=False)),
                ('was_absent', models.BooleanField(default=False)),
                ('absence_acknowledged', models.BooleanField(default=False)),
                ('history_id', models.AutoField(serialize=False, primary_key=True)),
                ('history_date', models.DateTimeField()),
                ('history_type', models.CharField(max_length=1, choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')])),
                ('history_user', models.ForeignKey(related_name='+', on_delete=models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True)),
                ('scheduled_activity', models.ForeignKey(related_name='+', on_delete=models.deletion.DO_NOTHING,
                                                         db_constraint=False, blank=True, to='eighth.EighthScheduledActivity', null=True)),
                ('user', models.ForeignKey(related_name='+', on_delete=models.deletion.DO_NOTHING,
                                           db_constraint=False, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
                'verbose_name': 'historical eighth signup',
            },
        ),
        migrations.CreateModel(
            name='HistoricalEighthSponsor',
            fields=[
                ('id', models.IntegerField(verbose_name='ID', db_index=True, auto_created=True, blank=True)),
                ('created_time', models.DateTimeField(null=True, editable=False, blank=True)),
                ('last_modified_time', models.DateTimeField(null=True, editable=False, blank=True)),
                ('first_name', models.CharField(max_length=50)),
                ('last_name', models.CharField(max_length=50)),
                ('online_attendance', models.BooleanField(default=True)),
                ('show_full_name', models.BooleanField(default=False)),
                ('history_id', models.AutoField(serialize=False, primary_key=True)),
                ('history_date', models.DateTimeField()),
                ('history_type', models.CharField(max_length=1, choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')])),
                ('history_user', models.ForeignKey(related_name='+', on_delete=models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True)),
                ('user', models.ForeignKey(related_name='+', on_delete=models.deletion.DO_NOTHING,
                                           db_constraint=False, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
                'verbose_name': 'historical eighth sponsor',
            },
        ),
    ]
