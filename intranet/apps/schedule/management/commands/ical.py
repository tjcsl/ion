# -*- coding: utf-8 -*-

from datetime import datetime
from urllib import request

from django.core.management.base import BaseCommand

from icalendar import Calendar

from intranet.apps.schedule.models import CodeName, Day, DayType


class Command(BaseCommand):
    args = ''
    help = 'Adds schedule entries from iCal to the database.'

    def handle(self, *args, **options):

        def get_ical():
            resp = request.urlopen('http://www.calendarwiz.com/CalendarWiz_iCal.php?crd=tjhsstcalendar')
            ical = resp.read()
            return ical

        def parse(ical):
            cal = Calendar.from_ical(ical)
            calmap = {}
            for event in cal.walk('vevent'):
                date = event.get('dtstart')
                summary = event.get('summary')
                categories = event.get('categories')
                if categories in ['Blue Day', 'Red Day', 'Anchor Day']:
                    print("{} {} {}".format(date.to_ical(), summary, categories))
                    calmap[date.to_ical()] = str(summary)
            return calmap

        # FIXME I'M BROKEN
        def add(ical_map):
            for date, type in ical_map.items():
                # type = codename
                cns = CodeName.objects.filter(name=type)
                if len(cns) < 1:
                    cn = CodeName.objects.create(name=type)
                else:
                    cn = cns[0]
                # type object
                dts = DayType.objects.filter(codenames__in=cn)
                if len(dts) < 1:
                    dt = DayType.objects.create(name=cn.name)
                    dt.codenames.add(cn)
                    dt.save()
                else:
                    dt = dts[0]
                # day: ate
                day = datetime.strptime(date, '%Y%m%d')
                do = Day.objects.filter(date=day)
                if len(do) < 1:
                    daydate = Day.objects.create(date=day, type=dt)
                    print(daydate)
                else:
                    print("{} already exists".format(str(daydate)))

        map = parse(get_ical())
        print(map)
        # add(map)
