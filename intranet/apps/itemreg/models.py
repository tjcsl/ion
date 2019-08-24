from django.conf import settings
from django.db import models


class CalculatorRegistration(models.Model):
    CALC_CHOICES = (
        ("ti83", "TI-83"),
        ("ti83p", "TI-83+"),
        ("ti84p", "TI-84+"),
        ("ti84pse", "TI-84+ Silver Edition"),
        ("ti84pcse", "TI-84+ C Silver Edition"),
        ("ti84pce", "TI-84+ CE"),
        ("ti89", "TI-89"),
        ("nspirecx", "TI-Nspire CX"),
        ("nspirecas", "TI-Nspire CAS"),
        ("otherti", "Other TI"),
        ("other", "Other"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)
    calc_serial = models.CharField(max_length=10)
    calc_id = models.CharField(max_length=14)
    calc_type = models.CharField(max_length=10, choices=CALC_CHOICES)
    added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{}'s {}".format(self.user.full_name, self.get_calc_type_display())  # get_FIELD_display() is defined by models.Model


class ComputerRegistration(models.Model):
    MANUF_CHOICES = (
        ("acer", "Acer"),
        ("apple", "Apple"),
        ("asus", "Asus"),
        ("dell", "Dell"),
        ("hp", "HP"),
        ("lenovo", "Lenovo"),
        ("toshiba", "Toshiba"),
        ("ibm", "IBM"),
        ("compaq", "Compaq"),
        ("fujitsu", "Fujitsu"),
        ("vizio", "Vizio"),
        ("other", "Other"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)
    manufacturer = models.CharField(max_length=15, choices=MANUF_CHOICES)
    model = models.CharField(max_length=100)
    serial = models.CharField(max_length=20)
    description = models.TextField(max_length=1000)
    screen_size = models.PositiveIntegerField()
    added = models.DateTimeField(auto_now_add=True)

    @property
    def computer_name(self) -> str:
        """Returns a description of the computer, formatted as <screen size>" <manufacturer> <model>.

        Returns:
            A nicely formatted description of the computer.

        """
        return '{}" {} {}'.format(self.screen_size, self.get_manufacturer_display(), self.model)

    def __str__(self):
        return "{}'s {}".format(self.user.full_name, self.computer_name)


class PhoneRegistration(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)
    MANUF_CHOICES = (
        ("samsung", "Samsung"),
        ("apple", "Apple"),
        ("motorola", "Motorola"),
        ("huawei", "Huawei"),
        ("lg", "LG"),
        ("xiaomi", "Xiaomi"),
        ("zte", "ZTE"),
        ("nokia", "Nokia"),
        ("other", "Other"),
    )
    manufacturer = models.CharField(max_length=15, choices=MANUF_CHOICES)
    model = models.CharField(max_length=100)
    serial = models.CharField(max_length=20)
    description = models.TextField(max_length=1000)
    added = models.DateTimeField(auto_now_add=True)

    @property
    def phone_name(self) -> str:
        """Returns a description of the phone, formatted as <manufacturer> <model>.

        Returns:
            A nicely formatted description of the phone.

        """
        return "{} {}".format(self.get_manufacturer_display(), self.model)

    def __str__(self):
        return "{}'s {}".format(self.user.full_name, self.model)
