# Generated by Django 3.2.25 on 2024-04-01 02:04

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('eighth', '0069_alter_eighthsponsor_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='eighthactivity',
            name='club_sponsors',
            field=models.ManyToManyField(blank=True, related_name='club_sponsor_for_set', to=settings.AUTH_USER_MODEL),
        ),
    ]
