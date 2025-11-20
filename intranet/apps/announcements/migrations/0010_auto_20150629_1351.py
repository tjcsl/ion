# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('announcements', '0009_announcement_expiration_date')]

    operations = [migrations.AlterField(
        model_name='announcement',
        name='author',
        field=models.CharField(max_length=63, blank=True),
    )]
