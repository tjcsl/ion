# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name='NotificationConfig',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('android_gcm_token', models.CharField(max_length=100, null=True, blank=True)),
                ('android_gcm_rand', models.CharField(max_length=100, null=True, blank=True)),
                ('android_gcm_time', models.DateTimeField(null=True, blank=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
        ),
    ]
