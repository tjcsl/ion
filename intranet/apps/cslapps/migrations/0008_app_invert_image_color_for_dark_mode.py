# Generated by Django 3.2.17 on 2023-04-06 21:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cslapps', '0007_remove_app_available_to_all'),
    ]

    operations = [
        migrations.AddField(
            model_name='app',
            name='invert_image_color_for_dark_mode',
            field=models.BooleanField(default=False),
        ),
    ]
