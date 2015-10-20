# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from intranet import settings
from intranet.apps.eighth.models import EighthActivity


class Command(BaseCommand):
    help = "Check if there are any blank AIDs, and replace them with their current internal ID number."

    def handle(self, **options):
        """
        all_activities = EighthActivity.objects.all()
        for act in all_activities:
            if not act.aid:
                self.stdout.write("{}\t{}\tAID defaulted to ID number.".format(act.id, act))
                act.aid = act.id
                act.save()
            else:
                self.stdout.write("{}\t{}\tOK.".format(act.id, act))
        """
        self.stdout.write("Done.")