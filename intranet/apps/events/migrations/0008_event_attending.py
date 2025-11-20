# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL), ('events', '0007_auto_20150628_1227')]

    operations = [
        migrations.AddField(
            model_name='event',
            name='attending',
            field=models.ManyToManyField(related_name='attending', to=settings.AUTH_USER_MODEL, blank=True),
        )
    ]
