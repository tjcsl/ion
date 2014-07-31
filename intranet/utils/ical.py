from icalendar import Calendar, Event
from datetime import datetime
#from intranet.apps.schedule.models import *
import urllib2

def get_ical():
    resp = urllib2.urlopen('http://www.calendarwiz.com/CalendarWiz_iCal.php?crd=tjhsstcalendar')
    ical = resp.read()
    return ical

def parse(ical):
    cal = Calendar.from_ical(ical)
    map = {}
    for event in cal.walk('vevent'):
        date = event.get('dtstart')
        summary = event.get('summary')
        categories = event.get('categories')
        if categories in ['Blue Day','Red Day','Anchor Day']:
            print "{} {} {}".format(date.to_ical(), summary, categories)
            map[date.to_ical()] = unicode(summary)

    return map



map = parse(get_ical())
print map
