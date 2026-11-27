from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("itemreg", "0010_auto_20210122_1145"),
    ]

    operations = [
        migrations.AlterField(
            model_name="calculatorregistration",
            name="calc_type",
            field=models.CharField(
                choices=[
                    ("ti83", "TI-83"),
                    ("ti83p", "TI-83+"),
                    ("ti84p", "TI-84+"),
                    ("ti84pse", "TI-84+ Silver Edition"),
                    ("ti84pcse", "TI-84+ C Silver Edition"),
                    ("ti84pce", "TI-84+ CE"),
                    ("ti84evo", "TI-84 Evo"),
                    ("ti89", "TI-89"),
                    ("nspirecx", "TI-Nspire CX"),
                    ("nspirecas", "TI-Nspire CAS"),
                    ("numworks", "NumWorks"),
                    ("otherti", "Other TI"),
                    ("other", "Other"),
                ],
                max_length=10,
            ),
        ),
    ]
