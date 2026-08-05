from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0042_user_seen_april_fools'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='administrator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='administered_students', to=settings.AUTH_USER_MODEL),
        ),
    ]
