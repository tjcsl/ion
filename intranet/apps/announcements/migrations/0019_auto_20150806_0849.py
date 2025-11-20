# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('announcements', '0018_announcement_notify_post')]

    operations = [
        migrations.AlterModelOptions(
            name='announcement',
            options={'ordering': ['-added', '-pinned']},
        ),
        migrations.AddField(
            model_name='announcement',
            name='pinned',
            field=models.BooleanField(default=False),
        ),
    ]
