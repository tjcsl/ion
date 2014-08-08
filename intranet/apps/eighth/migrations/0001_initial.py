# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'EighthSponsor'
        db.create_table(u'eighth_eighthsponsor', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=63, null=True)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=63, null=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['users.User'], null=True)),
            ('online_attendance', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal(u'eighth', ['EighthSponsor'])

        # Adding unique constraint on 'EighthSponsor', fields ['first_name', 'last_name', 'user', 'online_attendance']
        db.create_unique(u'eighth_eighthsponsor', ['first_name', 'last_name', 'user_id', 'online_attendance'])

        # Adding model 'EighthRoom'
        db.create_table(u'eighth_eighthroom', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=63)),
            ('capacity', self.gf('django.db.models.fields.SmallIntegerField')(default=-1)),
        ))
        db.send_create_signal(u'eighth', ['EighthRoom'])

        # Adding model 'EighthActivity'
        db.create_table(u'eighth_eighthactivity', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=63)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('restricted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('presign', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('one_a_day', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('both_blocks', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('sticky', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('special', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'eighth', ['EighthActivity'])

        # Adding M2M table for field sponsors on 'EighthActivity'
        m2m_table_name = db.shorten_name(u'eighth_eighthactivity_sponsors')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('eighthactivity', models.ForeignKey(orm[u'eighth.eighthactivity'], null=False)),
            ('eighthsponsor', models.ForeignKey(orm[u'eighth.eighthsponsor'], null=False))
        ))
        db.create_unique(m2m_table_name, ['eighthactivity_id', 'eighthsponsor_id'])

        # Adding M2M table for field rooms on 'EighthActivity'
        m2m_table_name = db.shorten_name(u'eighth_eighthactivity_rooms')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('eighthactivity', models.ForeignKey(orm[u'eighth.eighthactivity'], null=False)),
            ('eighthroom', models.ForeignKey(orm[u'eighth.eighthroom'], null=False))
        ))
        db.create_unique(m2m_table_name, ['eighthactivity_id', 'eighthroom_id'])

        # Adding model 'EighthBlock'
        db.create_table(u'eighth_eighthblock', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('block_letter', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('locked', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'eighth', ['EighthBlock'])

        # Adding unique constraint on 'EighthBlock', fields ['date', 'block_letter']
        db.create_unique(u'eighth_eighthblock', ['date', 'block_letter'])

        # Adding model 'EighthScheduledActivity'
        db.create_table(u'eighth_eighthscheduledactivity', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('block', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['eighth.EighthBlock'])),
            ('activity', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['eighth.EighthActivity'])),
            ('comments', self.gf('django.db.models.fields.CharField')(max_length=255, null=True)),
            ('capacity', self.gf('django.db.models.fields.SmallIntegerField')(null=True)),
            ('attendance_taken', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('cancelled', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'eighth', ['EighthScheduledActivity'])

        # Adding unique constraint on 'EighthScheduledActivity', fields ['block', 'activity']
        db.create_unique(u'eighth_eighthscheduledactivity', ['block_id', 'activity_id'])

        # Adding M2M table for field sponsors on 'EighthScheduledActivity'
        m2m_table_name = db.shorten_name(u'eighth_eighthscheduledactivity_sponsors')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('eighthscheduledactivity', models.ForeignKey(orm[u'eighth.eighthscheduledactivity'], null=False)),
            ('eighthsponsor', models.ForeignKey(orm[u'eighth.eighthsponsor'], null=False))
        ))
        db.create_unique(m2m_table_name, ['eighthscheduledactivity_id', 'eighthsponsor_id'])

        # Adding M2M table for field rooms on 'EighthScheduledActivity'
        m2m_table_name = db.shorten_name(u'eighth_eighthscheduledactivity_rooms')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('eighthscheduledactivity', models.ForeignKey(orm[u'eighth.eighthscheduledactivity'], null=False)),
            ('eighthroom', models.ForeignKey(orm[u'eighth.eighthroom'], null=False))
        ))
        db.create_unique(m2m_table_name, ['eighthscheduledactivity_id', 'eighthroom_id'])

        # Adding model 'EighthSignup'
        db.create_table(u'eighth_eighthsignup', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['users.User'])),
            ('scheduled_activity', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['eighth.EighthScheduledActivity'])),
            ('after_deadline', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'eighth', ['EighthSignup'])

        # Adding unique constraint on 'EighthSignup', fields ['user', 'scheduled_activity']
        db.create_unique(u'eighth_eighthsignup', ['user_id', 'scheduled_activity_id'])

        # Adding model 'EighthAbsence'
        db.create_table(u'eighth_eighthabsence', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('block', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['eighth.EighthBlock'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['users.User'])),
        ))
        db.send_create_signal(u'eighth', ['EighthAbsence'])

        # Adding unique constraint on 'EighthAbsence', fields ['block', 'user']
        db.create_unique(u'eighth_eighthabsence', ['block_id', 'user_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'EighthAbsence', fields ['block', 'user']
        db.delete_unique(u'eighth_eighthabsence', ['block_id', 'user_id'])

        # Removing unique constraint on 'EighthSignup', fields ['user', 'scheduled_activity']
        db.delete_unique(u'eighth_eighthsignup', ['user_id', 'scheduled_activity_id'])

        # Removing unique constraint on 'EighthScheduledActivity', fields ['block', 'activity']
        db.delete_unique(u'eighth_eighthscheduledactivity', ['block_id', 'activity_id'])

        # Removing unique constraint on 'EighthBlock', fields ['date', 'block_letter']
        db.delete_unique(u'eighth_eighthblock', ['date', 'block_letter'])

        # Removing unique constraint on 'EighthSponsor', fields ['first_name', 'last_name', 'user', 'online_attendance']
        db.delete_unique(u'eighth_eighthsponsor', ['first_name', 'last_name', 'user_id', 'online_attendance'])

        # Deleting model 'EighthSponsor'
        db.delete_table(u'eighth_eighthsponsor')

        # Deleting model 'EighthRoom'
        db.delete_table(u'eighth_eighthroom')

        # Deleting model 'EighthActivity'
        db.delete_table(u'eighth_eighthactivity')

        # Removing M2M table for field sponsors on 'EighthActivity'
        db.delete_table(db.shorten_name(u'eighth_eighthactivity_sponsors'))

        # Removing M2M table for field rooms on 'EighthActivity'
        db.delete_table(db.shorten_name(u'eighth_eighthactivity_rooms'))

        # Deleting model 'EighthBlock'
        db.delete_table(u'eighth_eighthblock')

        # Deleting model 'EighthScheduledActivity'
        db.delete_table(u'eighth_eighthscheduledactivity')

        # Removing M2M table for field sponsors on 'EighthScheduledActivity'
        db.delete_table(db.shorten_name(u'eighth_eighthscheduledactivity_sponsors'))

        # Removing M2M table for field rooms on 'EighthScheduledActivity'
        db.delete_table(db.shorten_name(u'eighth_eighthscheduledactivity_rooms'))

        # Deleting model 'EighthSignup'
        db.delete_table(u'eighth_eighthsignup')

        # Deleting model 'EighthAbsence'
        db.delete_table(u'eighth_eighthabsence')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'eighth.eighthabsence': {
            'Meta': {'unique_together': "((u'block', u'user'),)", 'object_name': 'EighthAbsence'},
            'block': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['eighth.EighthBlock']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.User']"})
        },
        u'eighth.eighthactivity': {
            'Meta': {'object_name': 'EighthActivity'},
            'both_blocks': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '63'}),
            'one_a_day': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'presign': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'restricted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'rooms': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['eighth.EighthRoom']", 'symmetrical': 'False', 'blank': 'True'}),
            'special': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'sponsors': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['eighth.EighthSponsor']", 'symmetrical': 'False', 'blank': 'True'}),
            'sticky': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'eighth.eighthblock': {
            'Meta': {'unique_together': "((u'date', u'block_letter'),)", 'object_name': 'EighthBlock'},
            'activities': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['eighth.EighthActivity']", 'symmetrical': 'False', 'through': u"orm['eighth.EighthScheduledActivity']", 'blank': 'True'}),
            'block_letter': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'locked': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'eighth.eighthroom': {
            'Meta': {'object_name': 'EighthRoom'},
            'capacity': ('django.db.models.fields.SmallIntegerField', [], {'default': '-1'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '63'})
        },
        u'eighth.eighthscheduledactivity': {
            'Meta': {'unique_together': "((u'block', u'activity'),)", 'object_name': 'EighthScheduledActivity'},
            'activity': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['eighth.EighthActivity']"}),
            'attendance_taken': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'block': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['eighth.EighthBlock']"}),
            'cancelled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'capacity': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True'}),
            'comments': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['users.User']", 'through': u"orm['eighth.EighthSignup']", 'symmetrical': 'False'}),
            'rooms': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['eighth.EighthRoom']", 'symmetrical': 'False'}),
            'sponsors': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['eighth.EighthSponsor']", 'symmetrical': 'False'})
        },
        u'eighth.eighthsignup': {
            'Meta': {'unique_together': "((u'user', u'scheduled_activity'),)", 'object_name': 'EighthSignup'},
            'after_deadline': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'scheduled_activity': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['eighth.EighthScheduledActivity']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.User']"})
        },
        u'eighth.eighthsponsor': {
            'Meta': {'unique_together': "((u'first_name', u'last_name', u'user', u'online_attendance'),)", 'object_name': 'EighthSponsor'},
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '63', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '63', 'null': 'True'}),
            'online_attendance': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.User']", 'null': 'True'})
        },
        u'users.user': {
            'Meta': {'object_name': 'User'},
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        }
    }

    complete_apps = ['eighth']