# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('announcements', '0021_announcement_notify_email_all')]

    operations = [migrations.AlterField(
        model_name='announcementrequest',
        name='notes',
        field=models.TextField(blank=True),
    )]
