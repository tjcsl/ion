# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0006_require_contenttypes_0002'),
        ('eighth', '0024_eighthactivity_aid'),
        ('announcements', '0009_announcement_expiration_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=10000)),
                ('created_time', models.DateTimeField(auto_now=True)),
                ('last_modified_time', models.DateTimeField(auto_now_add=True)),
                ('time', models.DateTimeField(auto_now=True)),
                ('location', models.CharField(max_length=100)),
                ('announcement', models.ForeignKey(to='announcements.Announcement', null=True, on_delete=models.CASCADE)),
                ('groups', models.ManyToManyField(to='auth.Group', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Link',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField(max_length=2000)),
            ],
        ),
        migrations.AddField(
            model_name='event',
            name='links',
            field=models.ManyToManyField(to='events.Link'),
        ),
        migrations.AddField(
            model_name='event',
            name='scheduled_activity',
            field=models.ForeignKey(to='eighth.EighthScheduledActivity', null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='event',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
        ),
    ]
