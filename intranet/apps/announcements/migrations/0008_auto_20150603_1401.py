# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('announcements', '0007_announcementrequest')]

    operations = [
        migrations.AlterField(
            model_name='announcementrequest',
            name='teachers_requested',
            field=models.ManyToManyField(related_name='teachers_requested', to=settings.AUTH_USER_MODEL),
        )
    ]
