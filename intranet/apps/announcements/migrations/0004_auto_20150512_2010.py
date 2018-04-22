# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('announcements', '0003_announcement_user')]

    operations = [
        migrations.AlterField(
            model_name='announcement',
            name='groups',
            field=models.ManyToManyField(to='auth.Group', blank=True),
        ),
        migrations.AlterField(
            model_name='announcement',
            name='user',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
        ),
    ]
