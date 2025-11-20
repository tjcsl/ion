# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL), ('notifications', '0002_auto_20150729_1734')]

    operations = [
        migrations.CreateModel(
            name='GCMNotification',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('multicast_id', models.CharField(max_length=250)),
                ('num_success', models.IntegerField(default=0)),
                ('num_failure', models.IntegerField(default=0)),
                ('sent_data', models.CharField(max_length=10000)),
                ('time', models.DateTimeField(auto_now=True)),
                ('sent_to', models.ManyToManyField(to='notifications.NotificationConfig')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
        ),
    ]
