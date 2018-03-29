# This file contains logic for server-side rendered pages
from django.utils import timezone

from ..announcements.models import Announcement


def hello_world(page, sign, request):
    return {"message": "{} from {} says Hello".format(page.name, sign.name)}


def announcements(page, sign, request):
    return {"public_announcements": Announcement.objects.filter(groups__isnull=True, expiration_date__gt=timezone.now())}
