# Generated by Django 3.2.17 on 2023-03-31 00:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0040_user_oauth_and_api_access'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='enable_april_fools',
            field=models.BooleanField(default=False),
        ),
    ]
