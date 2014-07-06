""" Common """
import datetime
import time
from django.shortcuts import redirect, render
from intranet.apps.auth.decorators import eighth_admin_required
import logging
logger = logging.getLogger(__name__)
def unmatch(match):
    """Takes a string like block/1/activity/2/group/3 and
       returns a dictionary of {'block': 1, 'activity': 2, 'group': 3}
    """

    if match is None:
        return {}

    spl = match.split('/')
    keys = spl[::2]
    values = spl[1::2]
    return dict(zip(keys, values))

def parse_date(date):
    """Takes a string of a date like 04/01/2014 and
       returns a datetime object used in a DateField
    """
    # Make a time.struct_time object out of the string
    structtime = time.strptime(date, "%m/%d/%Y")
    # Convert to datetime format
    dtime = datetime.datetime(*structtime[:6])
    return dtime

def get_startdate_obj(request):
    """
    Get the current startdate in request.session.
    """
    return request.session.get('startdate', '')

def get_startdate_fallback(request=None):
    """
    Get the current startdate in request.session, OR 
    fall back on the current date.
    """
    cd = datetime.datetime.now()
    if request is not None and request.session is not None:
        d = request.session.get('startdate', cd)
    else:
        d = cd
    return d

def get_startdate_str(request):
    """
    Get the start date (with fallback) as a string (for URLs)
    """
    return datetime.datetime.strftime(get_startdate_fallback(request), "%m/%d/%Y")

@eighth_admin_required
def eighth_startdate(request):
    # In format MM/DD/YYYY
    if 'startdate' not in request.session or request.session['startdate'] == '':
        d = datetime.datetime.now()
        request.session['startdate'] = d
    if 'confirm' in request.POST and 'date' in request.POST:
        da = request.POST.get('date')
        request.session['startdate'] = datetime.datetime.strptime(da, "%m/%d/%Y")
        next = request.POST.get('next', request.GET.get('next', 'eighth/admin'))
        return redirect("/{}".format(next[1:]))
    else:
        return render(request, "eighth/startdate.html", {
            "page": "eighth_admin",
            "template": True,
            "date": get_startdate_str(request) #request.session['startdate']
        })

@eighth_admin_required
def eighth_confirm_view(request, action=None, postfields=None):
    if action is None:
        action = "complete this operation"

    if postfields is None:
        postfields = {}

    return render(request, "eighth/confirm.html", {
        "page": "eighth_admin",
        "action": action,
        "postfields": postfields
    })
