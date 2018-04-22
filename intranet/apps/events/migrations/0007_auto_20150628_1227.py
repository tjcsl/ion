# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('events', '0006_auto_20150623_1615')]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='announcement',
            field=models.ForeignKey(blank=True, to='announcements.Announcement', null=True, on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='event',
            name='links',
            field=models.ManyToManyField(to='events.Link', blank=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='scheduled_activity',
            field=models.ForeignKey(blank=True, to='eighth.EighthScheduledActivity', null=True, on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='event',
            name='time',
            field=models.DateTimeField(),
        ),
    ]
