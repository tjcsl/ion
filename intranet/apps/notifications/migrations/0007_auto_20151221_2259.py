# -*- coding: utf-8 -*-

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [('notifications', '0006_auto_20151221_2028')]

    operations = [migrations.RenameField(
        model_name='notificationconfig',
        old_name='android_gcm_optout',
        new_name='gcm_optout',
    )]
