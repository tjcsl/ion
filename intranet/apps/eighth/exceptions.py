from django import http
from rest_framework import status
from collections import namedtuple

m = namedtuple("Message", ["regular", "admin"])


class SignupException(Exception):
    _messages = {
        "SignupForbidden": m("You may not sign this student up for activities.",
                             "You may not sign this student up for activities. This should not be happening - "
                             "contact an Intranet administrator."),
        "ScheduledActivityCancelled": m("This activity has been cancelled for this block.",
                                        "This activity has been cancelled for this block."),
        "ActivityDeleted": m("This activity has been deleted.",
                             "This activity has been deleted."),
        "ActivityFull": m("This activity is full. You may not sign up for it at this time.",
                          "This activity is full."),
        "BlockLocked": m("This block has been locked. Signup is not allowed at this time.",
                         "This block has been locked."),
        "Presign": m("You may not sign up for this activity more than two days in advance.",
                     "This activity can't be signed up for more two days in advance."),
        "Sticky": m("You may not switch out of a sticky activity.",
                    "This student is already in a sticky activity."),
        "OneADay": m("You may only sign up for this activity once per day.",
                     "This is a one-a-day activity."),
        "Restricted": m("You may not sign up for this restricted activity.",
                        "This activity is restricted for this student.")
    }

    def __init__(self):
        self.errors = set()

    def __repr__(self):
        return "SignupException(" + ", ".join(self.errors) + ")"

    def __setattr__(self, name, value):
        if name in SignupException._messages:
            if value:
                self.errors.add(name)
            elif name in self.errors:
                self.errors.remove(name)
        super(SignupException, self).__setattr__(name, value)

    def messages(self, admin=False):
        if admin:
            a = "admin"
        else:
            a = "regular"

        return [getattr(SignupException._messages[e], a) for e in self.errors]

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

        return http.HttpResponse(response,
                                 content_type=content_type,
                                 status=status.HTTP_403_FORBIDDEN)
