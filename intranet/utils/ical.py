# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from icalendar import Calendar, Event
from datetime import datetime
#from intranet.apps.schedule.models import *
from six import text_type
from six.moves.urllib import request


def get_ical():
    resp = request.urlopen('http://www.calendarwiz.com/CalendarWiz_iCal.php?crd=tjhsstcalendar')
    ical = resp.read()
    return ical


def parse(ical):
    cal = Calendar.from_ical(ical)
    map = {}
    for event in cal.walk('vevent'):
        date = event.get('dtstart')
        summary = event.get('summary')
        categories = event.get('categories')
        if categories in ['Blue Day', 'Red Day', 'Anchor Day']:
            print("{} {} {}".format(date.to_ical(), summary, categories))
            map[date.to_ical()] = text_type(summary)

    return map

if __name__ == '__main__':
    map = parse(get_ical())
    print(map)
