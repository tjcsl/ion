# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('announcements', '0020_auto_20150806_1547')]

    operations = [migrations.AddField(
        model_name='announcement',
        name='notify_email_all',
        field=models.BooleanField(default=False),
    )]
