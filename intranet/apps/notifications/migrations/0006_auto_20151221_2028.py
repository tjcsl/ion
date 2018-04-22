# -*- coding: utf-8 -*-

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [('notifications', '0005_auto_20151221_2008')]

    operations = [
        migrations.RenameField(
            model_name='notificationconfig',
            old_name='android_gcm_time',
            new_name='gcm_time',
        ),
        migrations.RenameField(
            model_name='notificationconfig',
            old_name='android_gcm_token',
            new_name='gcm_token',
        ),
        migrations.RemoveField(
            model_name='notificationconfig',
            name='chrome_gcm_time',
        ),
        migrations.RemoveField(
            model_name='notificationconfig',
            name='chrome_gcm_token',
        ),
    ]
