# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL), ('events', '0012_auto_20150913_1433')]

    operations = [
        migrations.AddField(
            model_name='event',
            name='rejected_by',
            field=models.ForeignKey(related_name='rejected_event', to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='event',
            name='approved_by',
            field=models.ForeignKey(related_name='approved_event', to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
        ),
    ]
