# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL), ('announcements', '0015_auto_20150723_0922')]

    operations = [
        migrations.CreateModel(
            name='AnnouncementUserMap',
            fields=[('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True))],
        ),
        migrations.RemoveField(
            model_name='announcement',
            name='users_hidden',
        ),
        migrations.RemoveField(
            model_name='announcement',
            name='users_seen',
        ),
        migrations.AddField(
            model_name='announcementusermap',
            name='announcement',
            field=models.OneToOneField(to='announcements.Announcement', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='announcementusermap',
            name='users_hidden',
            field=models.ManyToManyField(related_name='announcements_hidden', to=settings.AUTH_USER_MODEL, blank=True),
        ),
        migrations.AddField(
            model_name='announcementusermap',
            name='users_seen',
            field=models.ManyToManyField(related_name='announcements_seen', to=settings.AUTH_USER_MODEL, blank=True),
        ),
    ]
