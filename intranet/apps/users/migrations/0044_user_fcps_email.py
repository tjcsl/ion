from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0043_user_administrator"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="fcps_email",
            field=models.EmailField(blank=True, default="", max_length=254),
        ),
    ]
