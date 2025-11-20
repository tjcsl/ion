# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('announcements', '0016_auto_20150723_1052')]

    operations = [
        migrations.AlterField(
            model_name='announcementusermap',
            name='announcement',
            field=models.OneToOneField(related_name='_user_map', to='announcements.Announcement', on_delete=models.CASCADE),
        )
    ]
