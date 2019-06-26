from django.conf import settings
from django.db import models


class CarApplication(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="carapplication", on_delete=models.CASCADE)
    license_plate = models.CharField(max_length=20)
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    added = models.DateTimeField(auto_now=True)
    updated = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{} {} {} ({})".format(self.year, self.make, self.model, self.license_plate)


class ParkingApplication(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="parkingapplication", on_delete=models.CASCADE)
    joint_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="parkingapplication_joint", on_delete=models.CASCADE)
    cars = models.ManyToManyField(CarApplication)
    email = models.CharField(max_length=50)
    mentorship = models.BooleanField(default=False)
    added = models.DateTimeField(auto_now=True)
    updated = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        s = "Parking Application for {}".format(self.user)
        if self.joint_user:
            s += " and jointly {}".format(self.joint_user)
        return s
