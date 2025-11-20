# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('announcements', '0014_auto_20150723_0914')]

    operations = [
        migrations.AlterField(
            model_name='announcement',
            name='users_hidden',
            field=models.ManyToManyField(related_name='announcements_hidden', to=settings.AUTH_USER_MODEL, blank=True),
        ),
        migrations.AlterField(
            model_name='announcement',
            name='users_seen',
            field=models.ManyToManyField(related_name='announcements_seen', to=settings.AUTH_USER_MODEL, blank=True),
        ),
    ]
