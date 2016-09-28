from django.db import models
from ..users.models import User


class HomecomingCourtNomination(models.Model):
    voter = models.ForeignKey(User, related_name="homecoming_court_nominations", on_delete=models.CASCADE)
    male_nominee = models.ForeignKey(User, related_name="homecoming_court_male_nominations", on_delete=models.CASCADE)
    female_nominee = models.ForeignKey(User, related_name="homecoming_court_female_nominations", on_delete=models.CASCADE)
