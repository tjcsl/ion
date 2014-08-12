from django import http
from rest_framework import status


class SignupException(Exception):
    def as_response(self):
        return http.HttpResponse(self.message, status=self.status)


class SignupForbidden(SignupException):
    message = "You may not sign this student up for activities."
    status = status.HTTP_403_FORBIDDEN


class ScheduledActivityCancelled(SignupException):
    message = "This activity has been cancelled for this block."
    status = status.HTTP_403_FORBIDDEN


class ActivityDeleted(SignupException):
    message = "This activity has been deleted."


class ActivityFull(SignupException):
    message = "This actity is full. You may not sign up for it at this time."
    status = status.HTTP_403_FORBIDDEN


class BlockLocked(SignupException):
    message = "This block has been locked. Signup is not allowed at this time."
    status = status.HTTP_403_FORBIDDEN


class Presign(SignupException):
    message = "You may not sign up for this activity more than two days in " \
              "advance."
    status = status.HTTP_403_FORBIDDEN


class Sticky(SignupException):
    message = "You may not switch out of a sticky activity."
    status = status.HTTP_403_FORBIDDEN


class OneADay(SignupException):
    message = "You may only sign up for this activity once per day."
    status = status.HTTP_403_FORBIDDEN


class Restricted(SignupException):
    message = "You may not sign up for this restricted activity."
    status = status.HTTP_403_FORBIDDEN
