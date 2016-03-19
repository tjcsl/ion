# -*- coding: utf-8 -*-
import json

from django.core.management.base import BaseCommand

from intranet.apps.notifications.views import gcm_post, get_gcm_schedule_uids
from intranet.apps.schedule.notifications import period_start_end_data
from intranet.apps.users.models import User


class Command(BaseCommand):
    help = "Send Google Cloud Messaging notifications at needed times at the beginning and end of a class period."

    def add_arguments(self, parser):
        parser.add_argument('--notify', action='store_true', dest='notify', default=False, help='notify')

    def do_notify(self, pd_data):
        users = get_gcm_schedule_uids()
        user = User.objects.get(id=9999)
        post, reqtext = gcm_post(users, pd_data, user=user)

    def handle(self, *args, **options):

        notify = options["notify"]
        pd_data = period_start_end_data(None)
        if pd_data:
            self.stdout.write(json.dumps(pd_data))

        if pd_data and notify:
            self.do_notify(pd_data)
