from django.db import models
from ..users.models import User

class LostItem(models.Model):
    user = models.ForeignKey(User)
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=1000)
    last_seen = models.DateField()
    added = models.DateTimeField(auto_now_add=True)


class FoundItem(models.Model):
    user = models.ForeignKey(User)
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=1000)
    found = models.DateField()
    added = models.DateTimeField(auto_now_add=True)


class CalculatorRegistration(models.Model):
    user = models.ForeignKey(User)
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


class ComputerRegistration(models.Model):
    user = models.ForeignKey(User)
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
    description = models.CharField(max_length=1000)
    screen_size = models.PositiveIntegerField()
    added = models.DateTimeField(auto_now_add=True)

class PhoneRegistration(models.Model):
    user = models.ForeignKey(User)
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
    description = models.CharField(max_length=1000)
    added = models.DateTimeField(auto_now_add=True)

