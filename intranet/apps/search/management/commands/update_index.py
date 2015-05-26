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
                    "ionid": get_attr(user, "iodineUidNumber"),
                    "id": get_attr(user, "iodineUidNumber"),
                    "ionusername": get_attr(user, "iodineUid"),
                    "username": get_attr(user, "iodineUid"),
                    "name": get_attr(user, "cn") if "displayName" not in user[1] else get_attr(user, "display_name"),
                    "commonname": get_attr(user, "cn"),
                    "displayname": get_attr(user, "displayName"),
                    "firstname": get_attr(user, "givenName"),
                    "fname": get_attr(user, "givenName"),
                    "middlename": get_attr(user, "middlename"),
                    "mname": get_attr(user, "middlename"),
                    "lastname": get_attr(user, "sn"),
                    "lname": get_attr(user, "sn"),
                    "nickname": get_attr(user, "nickname"),
                    "sex": None if "gender" not in user[1] else "female" if user[1]["gender"][0] == "F" else "male",
                    "graduationyear": int(user[1]["graduationYear"][0]) if "graduationYear" in user[1] else None,
                    "gradyear": int(user[1]["graduationYear"][0]) if "graduationYear" in user[1] else None
                }
            )
            i += 1
            if i % 100 == 0:
                self.stdout.write("Indexed {} users".format(i))
        self.stdout.write("Indexing complete")
