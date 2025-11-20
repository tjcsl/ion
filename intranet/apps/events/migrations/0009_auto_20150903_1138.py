# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('events', '0008_event_attending')]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='announcement',
            field=models.ForeignKey(related_name='event', blank=True, to='announcements.Announcement', null=True, on_delete=models.CASCADE),
        )
    ]
