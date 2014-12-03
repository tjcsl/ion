from django import http
from rest_framework import status


class SignupException(Exception):
    _messages = {
        "SignupForbidden": "You may not sign this student up for activities.",
        "ScheduledActivityCancelled": "This activity has been cancelled for this block.",
        "ActivityDeleted": "This activity has been deleted.",
        "ActivityFull": "This actity is full. You may not sign up for it at this time.",
        "BlockLocked": "This block has been locked. Signup is not allowed at this time.",
        "Presign": "You may not sign up for this activity more than two days in advance.",
        "Sticky": "You may not switch out of a sticky activity.",
        "OneADay": "You may only sign up for this activity once per day.",
        "Restricted": "You may not sign up for this restricted activity."
    }

    def __init__(self):
        self.errors = set()

    def __setattr__(self, name, value):
        if name in SignupException._messages:
            if value:
                self.errors.add(name)
            else:
                if name in self.errors:
                    self.errors.remove(name)
        super(SignupException, self).__setattr__(name, value)

    @property
    def messages(self):
        return [SignupException._messages[e] for e in self.errors]

    def as_response(self, html=True):
        if len(self.errors) <= 1:
            html = False

        if html:
            response = "<ul>"
            for message in self.messages:
                response += "<li>" + message + "</li>"
            response += "</ul>"
            content_type = "text/html"
        else:
            response = "\n".join(self.messages)
            content_type = "text/plain"

        return http.HttpResponse(response,
                                 content_type=content_type,
                                 status=status.HTTP_403_FORBIDDEN)
