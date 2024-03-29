# Generated by Django 3.2.18 on 2023-06-02 03:47

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('announcements', '0026_warningannouncement_active'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='warningannouncement',
            options={'ordering': ['-added']},
        ),
        migrations.AddField(
            model_name='warningannouncement',
            name='added',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
