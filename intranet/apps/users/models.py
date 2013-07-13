from django.db import models
from django.contrib.auth.models import AbstractBaseUser
# Add UserProfile model here


class User(AbstractBaseUser):
    username = models.CharField(max_length=40, unique=True, db_index=True)

    USERNAME_FIELD = 'username'

    def get_full_name():
        return "Angela Smith"

    def get_short_name():
        return "Angela"
