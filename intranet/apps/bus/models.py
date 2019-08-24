from django.db import models


class Route(models.Model):
    """A bus route (e.g. TJ-24)"""

    ARRIVAL_STATUSES = (("a", "Arrived (In the lot)"), ("d", "Delayed"), ("o", "On Time (Expected)"))

    route_name = models.CharField(max_length=30, unique=True)
    space = models.CharField(max_length=4, blank=True)
    bus_number = models.CharField(max_length=5, blank=True)
    status = models.CharField("arrival status", choices=ARRIVAL_STATUSES, max_length=1, default="o")

    def reset_status(self):
        """Reset status to (on time) """
        self.status = "o"
        self.space = ""
        self.save(update_fields=["status", "space"])

    def __str__(self):
        return self.route_name
