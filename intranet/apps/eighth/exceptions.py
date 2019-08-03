from collections import namedtuple

from rest_framework.status import HTTP_403_FORBIDDEN

from django.http import HttpResponse

m = namedtuple("Message", ["regular", "admin"])


class SignupException(Exception):
    _messages = {
        "SignupForbidden": m(
            "You may not sign this student up for activities.",
            "You may not sign this student up for activities. This should not be happening - contact an Intranet administrator.",
        ),
        "ScheduledActivityCancelled": m("This activity has been cancelled for this block.", "This activity has been cancelled for this block."),
        "ActivityDeleted": m(
            "This activity has been deleted. Refresh this page to see an up-to-date list of activities.", "This activity has been deleted."
        ),
        "ActivityFull": m("This activity is full. You may not sign up for it at this time.", "This activity is full."),
        "BlockLocked": m("This block has been locked. Signup is not allowed at this time.", "This block has been locked."),
        "Presign": m(
            "You may not sign up for this activity more than two days in advance.", "This activity can't be signed up for more two days in advance."
        ),
        "Sticky": m(
            "You may not switch out of a sticky activity.",
            "<strong style='font-size: 32px'><u>This student is already in a sticky activity.</u></strong>",
        ),
        "OneADay": m(
            "You may only sign up for this activity once per day. To sign up for the activity during this block, "
            "change your signup on the other block where you selected this activity.",
            "This is a one-a-day activity.",
        ),
        "Restricted": m(
            "You may not sign up for this restricted activity. You are not on the authorized list.", "This activity is restricted for this student."
        ),
        "Blacklisted": m("You are blacklisted from this activity.", "This student is blacklisted from this activity."),
        "OverrideBlockLocked": m(
            "An override block ({0}) has been locked. Signup is not allowed at this time.", "An override block ({1}) has been locked."
        ),
        "OverrideBlockPermissions": m(
            "Your signup ({0}) on an override block ({1}) cannot be changed out of. You will be unable to sign up for any activities on this block.",
            "Your signup ({0}) on an override block ({1}) cannot be changed out of.",
        ),
        "PrimaryEmailNotSet": m(
            "Please set a primary email in your preferences before joining the waitlist",
            "This user does not have a primary email set and cannot be added to a waitlist",
        ),
    }

    def __init__(self):
        super().__init__()
        self.errors = set()
        self.desc_errors = {}

    def __repr__(self):
        return "SignupException(%s)" % ", ".join(sorted(self.errors))

    def __str__(self):
        return ", ".join(sorted(self.errors))

    def __setattr__(self, name, value):
        if name in SignupException._messages:
            if isinstance(value, list):
                self.errors.add(name)
                self.desc_errors[name] = value
            elif value:
                self.errors.add(name)
            elif name in self.errors:
                self.errors.remove(name)
        super(SignupException, self).__setattr__(name, value)

    def messages(self, admin=False):
        if admin:
            a = "admin"
        else:
            a = "regular"

        msgs = []
        for e in sorted(self.errors):
            exc = SignupException._messages[e]
            if e in self.desc_errors:
                msgs.append(getattr(exc, a).format(*self.desc_errors[e]))
            else:
                msgs.append(getattr(exc, a))

        return msgs

    def as_response(self, html=True, admin=False):
        if len(self.errors) <= 1:
            html = False

        if html:
            response = "<ul>"
            for message in self.messages(admin=admin):
                response += "<li>" + message + "</li>"
            response += "</ul>"
            content_type = "text/html"
        else:
            response = "\n".join(self.messages(admin=admin))
            content_type = "text/plain"

        return HttpResponse(response, content_type=content_type, status=HTTP_403_FORBIDDEN)
