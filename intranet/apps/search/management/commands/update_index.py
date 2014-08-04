# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
from django.core.management.base import BaseCommand
import elasticsearch
from intranet import settings
from intranet.db import ldap_db


class Command(BaseCommand):
    help = "Updates the ElasticSearch index with user, class, and eighth period data"

    def handle(self, **options):
        # Destroy kerberos tickets to force simple auth
        os.system("kdestroy")

        attributes = ["iodineUidNumber",
                      "iodineUid",
                      "cn",
                      "displayName",
                      "givenName",
                      "middlename",
                      "sn",
                      "nickname",
                      "gender",
                      "graduationYear"]

        l = ldap_db.LDAPConnection()
        users = l.user_attributes(settings.USER_DN, attributes).results_array()

        def get_attr(user, a):
            return user[1].get(a, [None])[0]

        self.stdout.write("Indexing all users...")
        i = 0
        for user in users:
            es = elasticsearch.Elasticsearch()
            es.index(
                index=settings.ELASTICSEARCH_INDEX,
                doc_type=settings.ELASTICSEARCH_USER_DOC_TYPE,
                id=int(user[1]["iodineUidNumber"][0]),
                body={
                    "ion_id": get_attr(user, "iodineUidNumber"),
                    "ion_username": get_attr(user, "iodineUid"),
                    "common_name": get_attr(user, "cn"),
                    "display_name": get_attr(user, "displayName"),
                    "first_name": get_attr(user, "givenName"),
                    "middle_name": get_attr(user, "middlename"),
                    "last_name": get_attr(user, "sn"),
                    "nickname": get_attr(user, "nickname"),
                    "gender": None if "gender" not in user[1] else "female" if user[1]["gender"][0] == "F" else "male",
                    "graduation_year": int(user[1]["graduationYear"][0]) if "graduationYear" in user[1] else None
                }
            )
            i += 1
            if i % 100 == 0:
                self.stdout.write("Indexed {} users".format(i))
        self.stdout.write("Indexing complete")
