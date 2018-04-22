# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('users', '0003_merge')]

    operations = [
        migrations.AddField(
            model_name='user',
            name='receive_eighth_emails',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='receive_news_emails',
            field=models.BooleanField(default=False),
        ),
    ]
