from django.db import models
from ..users.models import User


class CalculatorRegistration(models.Model):
    user = models.ForeignKey(User, null=True)
    calc_serial = models.CharField(max_length=10)
    calc_id = models.CharField(max_length=14)
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
        ("other", "Other")
    )
    calc_type = models.CharField(max_length=10, choices=CALC_CHOICES)
    added = models.DateTimeField(auto_now_add=True)

    @property
    def calc_name(self):
        return {i[0]: i[1] for i in self.CALC_CHOICES}[self.calc_type]

    def __str__(self):
        return "{}'s {}".format(self.user.full_name, self.calc_name)


class ComputerRegistration(models.Model):
    user = models.ForeignKey(User, null=True)
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
        ("other", "Other")
    )
    manufacturer = models.CharField(max_length=15, choices=MANUF_CHOICES)
    model = models.CharField(max_length=100)
    serial = models.CharField(max_length=20)
    description = models.TextField(max_length=1000)
    screen_size = models.PositiveIntegerField()
    added = models.DateTimeField(auto_now_add=True)

    @property
    def manuf_name(self):
        return {i[0]: i[1] for i in self.MANUF_CHOICES}[self.manufacturer]

    @property
    def computer_name(self):
        return "{}\" {} {}".format(self.screen_size, self.manuf_name, self.model)

    def __str__(self):
        return "{}'s {}".format(self.user.full_name, self.computer_name)


class PhoneRegistration(models.Model):
    user = models.ForeignKey(User, null=True)
    MANUF_CHOICES = (
        ("samsung", "Samsung"),
        ("apple", "Apple"),
        ("motorola", "Motorola"),
        ("huawei", "Huawei"),
        ("lg", "LG"),
        ("xiaomi", "Xiaomi"),
        ("zte", "ZTE"),
        ("nokia", "Nokia"),
        ("other", "Other")
    )
    manufacturer = models.CharField(max_length=15, choices=MANUF_CHOICES)
    model = models.CharField(max_length=100)
    serial = models.CharField(max_length=20)
    description = models.TextField(max_length=1000)
    added = models.DateTimeField(auto_now_add=True)

    @property
    def manuf_name(self):
        return {i[0]: i[1] for i in self.MANUF_CHOICES}[self.manufacturer]

    @property
    def phone_name(self):
        return "{} {}".format(self.manuf_name, self.model)

    def __str__(self):
        return "{}'s {}".format(self.user.full_name, self.model)
