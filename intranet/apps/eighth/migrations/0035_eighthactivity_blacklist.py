# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('eighth', '0034_eighthscheduledactivity_special')]

    operations = [
        migrations.AddField(
            model_name='eighthactivity',
            name='users_blacklisted',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, blank=True),
            preserve_default=True,
        ),
    ]
