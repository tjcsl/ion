# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('announcements', '0017_auto_20150723_1058')]

    operations = [migrations.AddField(
        model_name='announcement',
        name='notify_post',
        field=models.BooleanField(default=True),
    )]
