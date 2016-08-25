# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from ....eighth.models import User
from ....groups.models import Group


class Command(BaseCommand):
    help = "Adds the specified user to the specified admin group"

    def add_arguments(self, parser):
        parser.add_argument('username')
        parser.add_argument('admin_group')

    def handle(self, *args, **options):
        g = Group.objects.get_or_create(name="admin_%s" % options['admin_group'])[0]
        User.get_user(username=options['username']).groups.add(g)
        self.stdout.write('Added %s to %s' % (options['username'], options['admin_group']))
