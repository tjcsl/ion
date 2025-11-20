# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('notifications', '0003_gcmnotification')]

    operations = [migrations.AddField(
        model_name='notificationconfig',
        name='android_gcm_optout',
        field=models.BooleanField(default=False),
    )]
