# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from intranet.apps.users.models import User
from intranet.apps.schedule.models import Day
from intranet.apps.schedule.views import schedule_context
from intranet.apps.notifications.views import gcm_post, get_gcm_schedule_uids


class Command(BaseCommand):
    help = "Send Google Cloud Messaging notifications at needed times at the beginning and end of a class period."

    def add_arguments(self, parser):
        parser.add_argument('--notify',
                            action='store_true',
                            dest='notify',
                            default=False,
                            help='notify')

    def do_notify(title, text):
        data = {
            "title": title,
            "text": text,
            "wakeup": True,
            "vibrate": True
        }
        users = get_gcm_schedule_uids()
        user = User.objects.get(id=9999)
        gcm_post(users, data, user)

    def handle(self, *args, **options):

        notify = options["notify"]


        