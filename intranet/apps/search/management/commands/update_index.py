# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
from django.core.management.base import BaseCommand
import elasticsearch
from intranet import settings
from intranet.db import ldap_db


class Command(BaseCommand):
    help = "Updates the ElasticSearch index with user data"

    def handle(self, **options):
        # Destroy kerberos tickets to force simple auth
        os.system("kdestroy")

        attributes = [
            "iodineUidNumber",
            "iodineUid",
            "cn",
            "displayName",
            "givenName",
            "middlename",
            "sn",
            "nickname",
            "gender",
            "graduationYear",
            "mobile",
            "homePhone",
            "telephoneNumber",
            "postalCode",
            "l",
            "street",
            "mail"
        ]

        l = ldap_db.LDAPConnection()
        users = l.user_attributes(settings.USER_DN, attributes).results_array()

        def get_attr(user, a):
            return user[1].get(a, [None])[0]

        def get_attr_list(user, a):
            return user[1].get(a, [])

        self.stdout.write("Indexing all users...")
        i = 0
        for user in users:
            # Determine some attributes
            if "displayName" not in user[1]:
                name = get_attr(user, "cn")
            else:
                name = get_attr(user, "displayName")

            if "gender" not in user[1]:
                sex = None
            elif user[1]["gender"][0] == "F":
                sex = "female"
            else:
                sex = "male"

            if "graduationYear" in user[1]:
                grad_year = int(user[1]["graduationYear"][0])
            else:
                grad_year = None

            phones = (get_attr_list(user, "homePhone") +
                      get_attr_list(user, "mobile") +
                      get_attr_list(user, "telephoneNumber"))

            # Index the user
            es = elasticsearch.Elasticsearch()
            es.index(
                index=settings.ELASTICSEARCH_INDEX,
                doc_type=settings.ELASTICSEARCH_USER_DOC_TYPE,
                id=int(user[1]["iodineUidNumber"][0]),
                body={
                    "ion_id": get_attr(user, "iodineUidNumber"),
                    "id": get_attr(user, "iodineUidNumber"),

                    "ion_username": get_attr(user, "iodineUid"),
                    "username": get_attr(user, "iodineUid"),

                    "name": name,
                    "common_name": get_attr(user, "cn"),
                    "display_name": get_attr(user, "displayName"),

                    "first": get_attr(user, "givenName"),
                    "firstname": get_attr(user, "givenName"),
                    "first_name": get_attr(user, "givenName"),

                    "middle": get_attr(user, "middlename"),
                    "middlename": get_attr(user, "middlename"),
                    "middle_name": get_attr(user, "middlename"),

                    "last": get_attr(user, "sn"),
                    "lastname": get_attr(user, "sn"),
                    "last_name": get_attr(user, "sn"),

                    "nickname": get_attr(user, "nickname"),
                    "nick": get_attr(user, "nickname"),

                    "sex": sex,

                    "gradyear": grad_year,
                    "graduation_year": grad_year,

                    "phone": phones,
                    "telephone": phones,

                    "zip": get_attr(user, "postalCode"),
                    "city": get_attr(user, "l"),
                    "address": get_attr(user, "street"),

                    "email": get_attr_list(user, "mail")
                }
            )
            i += 1
            if i % 100 == 0:
                self.stdout.write("Indexed {} users".format(i))
        self.stdout.write("Indexing complete")
