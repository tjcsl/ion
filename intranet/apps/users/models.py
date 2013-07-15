from intranet.db.ldap_db import Connection
from django.db import models
from django.contrib.auth.models import AbstractBaseUser


class UserManager(models.Manager):
    def return_something(self):
        return "something"


class User(AbstractBaseUser):
    username = models.CharField(max_length=50, unique=True, db_index=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    USERNAME_FIELD = 'username'
    objects = UserManager()

    def get_full_name(self):
        return self.first_name + " " + self.last_name

    def get_short_name(self):
        return self.first_name

    def get_phone(self):
        c = Connection()
        return c.user_attribute(self.username, 'homePhone')
    phone = property(get_phone)

    def get_street(self):
        c = Connection()
        return c.user_attribute(self.username, 'street')
    street = property(get_street)
