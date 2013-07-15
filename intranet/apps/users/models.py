from django.db import models
from django.contrib.auth.models import AbstractBaseUser


class UserManager(models.Manager):
    def return_something(self):
        return "something"
    # def with_counts(self):
    #     from django.db import connection
    #     cursor = connection.cursor()
    #     cursor.execute("""
    #         SELECT p.id, p.question, p.poll_date, COUNT(*)
    #         FROM polls_opinionpoll p, polls_response r
    #         WHERE p.id = r.poll_id
    #         GROUP BY p.id, p.question, p.poll_date
    #         ORDER BY p.poll_date DESC""")
    #     result_list = []
    #     for row in cursor.fetchall():
    #         p = self.model(id=row[0], question=row[1], poll_date=row[2])
    #         p.num_responses = row[3]
    #         result_list.append(p)
    #     return result_list


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
