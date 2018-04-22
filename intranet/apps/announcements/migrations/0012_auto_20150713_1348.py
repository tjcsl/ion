# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL), ('announcements', '0011_auto_20150713_1314')]

    operations = [
        migrations.AddField(
            model_name='announcementrequest',
            name='posted_by',
            field=models.ForeignKey(related_name='posted_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='announcementrequest',
            name='rejected',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='announcementrequest',
            name='rejected_by',
            field=models.ForeignKey(related_name='rejected_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='announcementrequest',
            name='user',
            field=models.ForeignKey(related_name='user', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
        ),
    ]
