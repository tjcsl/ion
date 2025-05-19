from django.db import migrations, models
import datetime
from ..models import shift_time
from ....settings.__init__ import ATTENDANCE_CODE_BUFFER

def populate_eighth_auto_fields(apps, schema_editor):
    Block = apps.get_model('schedule', 'Block')
    for obj in Block.objects.all():
        if "8" in obj.name:
            start = datetime.time(hour=obj.start.hour, minute=obj.start.minute)
            end = datetime.time(hour=obj.end.hour, minute=obj.end.minute)
            obj.eighth_auto_open = shift_time(start, -ATTENDANCE_CODE_BUFFER)
            obj.eighth_auto_close = shift_time(end, ATTENDANCE_CODE_BUFFER)
        else:
            obj.eighth_auto_open = None
            obj.eighth_auto_close = None
        obj.save()

class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0011_day_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='block',
            name='eighth_auto_close',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='block',
            name='eighth_auto_open',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.RunPython(populate_eighth_auto_fields, reverse_code=migrations.RunPython.noop),
    ]
