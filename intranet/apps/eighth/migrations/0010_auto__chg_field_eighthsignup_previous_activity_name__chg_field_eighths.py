# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'EighthSignup.previous_activity_name'
        db.alter_column(u'eighth_eighthsignup', 'previous_activity_name', self.gf('django.db.models.fields.CharField')(default='', max_length=100))

        # Changing field 'EighthSignup.previous_activity_sponsors'
        db.alter_column(u'eighth_eighthsignup', 'previous_activity_sponsors', self.gf('django.db.models.fields.CharField')(default='', max_length=100))

    def backwards(self, orm):

        # Changing field 'EighthSignup.previous_activity_name'
        db.alter_column(u'eighth_eighthsignup', 'previous_activity_name', self.gf('django.db.models.fields.CharField')(max_length=100, null=True))

        # Changing field 'EighthSignup.previous_activity_sponsors'
        db.alter_column(u'eighth_eighthsignup', 'previous_activity_sponsors', self.gf('django.db.models.fields.CharField')(max_length=100, null=True))

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
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'freshmen_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'groups_allowed': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'restricted_activity_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'juniors_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '63'}),
            'one_a_day': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'presign': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'restricted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'rooms': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['eighth.EighthRoom']", 'symmetrical': 'False', 'blank': 'True'}),
            'seniors_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'sophomores_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'special': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'sponsors': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['eighth.EighthSponsor']", 'symmetrical': 'False', 'blank': 'True'}),
            'sticky': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'users_allowed': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'restricted_activity_set'", 'blank': 'True', 'to': u"orm['users.User']"})
        },
        u'eighth.eighthblock': {
            'Meta': {'ordering': "(u'date', u'block_letter')", 'unique_together': "((u'date', u'block_letter'),)", 'object_name': 'EighthBlock'},
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
            'capacity': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'comments': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "u'eighthscheduledactivity_set'", 'symmetrical': 'False', 'through': u"orm['eighth.EighthSignup']", 'to': u"orm['users.User']"}),
            'rooms': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['eighth.EighthRoom']", 'symmetrical': 'False', 'blank': 'True'}),
            'sponsors': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['eighth.EighthSponsor']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'eighth.eighthsignup': {
            'Meta': {'unique_together': "((u'user', u'scheduled_activity'),)", 'object_name': 'EighthSignup'},
            'after_deadline': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pass_accepted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'previous_activity_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'previous_activity_sponsors': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'scheduled_activity': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'eighthsignup_set'", 'to': u"orm['eighth.EighthScheduledActivity']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.User']"}),
            'with_pass': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'eighth.eighthsponsor': {
            'Meta': {'unique_together': "((u'first_name', u'last_name', u'user', u'online_attendance'),)", 'object_name': 'EighthSponsor'},
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '63'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '63'}),
            'online_attendance': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['users.User']", 'unique': 'True', 'null': 'True', 'blank': 'True'})
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