# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('notifications', '0001_initial')]

    operations = [
        migrations.AlterField(
            model_name='notificationconfig',
            name='android_gcm_token',
            field=models.CharField(max_length=250, null=True, blank=True),
        )
    ]
