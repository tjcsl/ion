# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL), ('announcements', '0002_announcement_groups')]

    operations = [
        migrations.AddField(
            model_name='announcement',
            name='user',
            field=models.OneToOneField(null=True, blank=True, to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
        )
    ]
