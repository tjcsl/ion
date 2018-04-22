# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL), ('auth', '__first__')]

    operations = [
        migrations.CreateModel(
            name='EighthActivity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=63)),
                ('description', models.CharField(max_length=255, blank=True)),
                ('presign', models.BooleanField(default=False)),
                ('one_a_day', models.BooleanField(default=False)),
                ('both_blocks', models.BooleanField(default=False)),
                ('sticky', models.BooleanField(default=False)),
                ('special', models.BooleanField(default=False)),
                ('restricted', models.BooleanField(default=False)),
                ('freshmen_allowed', models.BooleanField(default=False)),
                ('sophomores_allowed', models.BooleanField(default=False)),
                ('juniors_allowed', models.BooleanField(default=False)),
                ('seniors_allowed', models.BooleanField(default=False)),
                ('deleted', models.BooleanField(default=False)),
                ('groups_allowed', models.ManyToManyField(related_name='restricted_activity_set', to='auth.Group', blank=True)),
            ],
            options={'verbose_name_plural': 'eighth activities'},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EighthBlock',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
                ('block_letter', models.CharField(max_length=1)),
                ('locked', models.BooleanField(default=False)),
            ],
            options={'ordering': ('date', 'block_letter')},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EighthRoom',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=63)),
                ('capacity', models.SmallIntegerField(default=-1)),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EighthScheduledActivity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('comments', models.CharField(max_length=255, blank=True)),
                ('capacity', models.SmallIntegerField(null=True, blank=True)),
                ('attendance_taken', models.BooleanField(default=False)),
                ('cancelled', models.BooleanField(default=False)),
                ('activity', models.ForeignKey(to='eighth.EighthActivity', on_delete=models.CASCADE)),
                ('block', models.ForeignKey(to='eighth.EighthBlock', on_delete=models.CASCADE)),
            ],
            options={'verbose_name_plural': 'eighth scheduled activities'},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EighthSignup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('time', models.DateTimeField(auto_now=True)),
                ('after_deadline', models.BooleanField(default=False)),
                ('previous_activity_name', models.CharField(max_length=100, blank=True)),
                ('previous_activity_sponsors', models.CharField(max_length=100, blank=True)),
                ('pass_accepted', models.BooleanField(default=False)),
                ('was_absent', models.BooleanField(default=False)),
                ('scheduled_activity',
                 models.ForeignKey(related_name='eighthsignup_set', to='eighth.EighthScheduledActivity', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EighthSponsor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('first_name', models.CharField(max_length=63)),
                ('last_name', models.CharField(max_length=63)),
                ('online_attendance', models.BooleanField(default=True)),
                ('user', models.OneToOneField(null=True, blank=True, to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='eighthsponsor',
            unique_together={('first_name', 'last_name', 'user', 'online_attendance')},
        ),
        migrations.AlterUniqueTogether(
            name='eighthsignup',
            unique_together={('user', 'scheduled_activity')},
        ),
        migrations.AddField(
            model_name='eighthscheduledactivity',
            name='members',
            field=models.ManyToManyField(related_name='eighthscheduledactivity_set', through='eighth.EighthSignup', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eighthscheduledactivity',
            name='rooms',
            field=models.ManyToManyField(to='eighth.EighthRoom', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eighthscheduledactivity',
            name='sponsors',
            field=models.ManyToManyField(to='eighth.EighthSponsor', blank=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='eighthscheduledactivity',
            unique_together={('block', 'activity')},
        ),
        migrations.AddField(
            model_name='eighthblock',
            name='activities',
            field=models.ManyToManyField(to='eighth.EighthActivity', through='eighth.EighthScheduledActivity', blank=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='eighthblock',
            unique_together={('date', 'block_letter')},
        ),
        migrations.AddField(
            model_name='eighthactivity',
            name='rooms',
            field=models.ManyToManyField(to='eighth.EighthRoom', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eighthactivity',
            name='sponsors',
            field=models.ManyToManyField(to='eighth.EighthSponsor', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eighthactivity',
            name='users_allowed',
            field=models.ManyToManyField(related_name='restricted_activity_set', to=settings.AUTH_USER_MODEL, blank=True),
            preserve_default=True,
        ),
    ]
