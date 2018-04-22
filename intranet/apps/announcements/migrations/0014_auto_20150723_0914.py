# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL), ('announcements', '0013_announcementrequest_admin_email_sent')]

    operations = [
        migrations.AddField(
            model_name='announcement',
            name='users_hidden',
            field=models.ManyToManyField(related_name='announcement_hidden', to=settings.AUTH_USER_MODEL, blank=True),
        ),
        migrations.AddField(
            model_name='announcement',
            name='users_seen',
            field=models.ManyToManyField(related_name='announcement_seen', to=settings.AUTH_USER_MODEL, blank=True),
        ),
    ]
