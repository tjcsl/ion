# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
import elasticsearch
from intranet import settings


class Command(BaseCommand):
    help = "Completely wipes the Elasticsearch index"

    def handle(self, **options):
        self.stdout.write("Removing user index...")
        es = elasticsearch.Elasticsearch()
        es.delete_by_query(
            index=settings.ELASTICSEARCH_INDEX,
            doc_type=settings.ELASTICSEARCH_USER_DOC_TYPE,
            body={
                "query": {
                    "match_all": {}
                }
            }
        )
        self.stdout.write("Removed user index.")
