# -*- coding: utf-8 -*-

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [('auth', '__first__')]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(default=django.utils.timezone.now, verbose_name='last login')),
                ('is_superuser',
                 models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.',
                                     verbose_name='superuser status')),
                ('username', models.CharField(unique=True, max_length=30)),
                ('groups',
                 models.ManyToManyField(
                     related_query_name='user', related_name='user_set', to='auth.Group', blank=True,
                     help_text='The groups this user belongs to. A user will get all permissions granted to each of his/her group.',
                     verbose_name='groups')),
                ('user_permissions',
                 models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Permission', blank=True,
                                        help_text='Specific permissions for this user.', verbose_name='user permissions')),
            ],
            options={'abstract': False},
            bases=(models.Model,),
        ),
    ]
