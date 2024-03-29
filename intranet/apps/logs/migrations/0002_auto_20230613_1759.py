# Generated by Django 3.2.18 on 2023-06-13 21:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logs', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='request',
            name='flag',
            field=models.CharField(blank=True, help_text='Flag this request for review by assigning it a label.', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='request',
            name='ip',
            field=models.CharField(max_length=255, verbose_name='IP address'),
        ),
    ]
