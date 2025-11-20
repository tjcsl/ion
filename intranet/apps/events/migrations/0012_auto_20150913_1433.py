# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('events', '0011_auto_20150913_1427')]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='approved_by',
            field=models.ForeignKey(related_name='rejected_event', to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
        )
    ]
