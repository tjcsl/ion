# -*- coding: utf-8 -*-

from copy import copy

from django.conf import settings
from django.utils import log
from django.views.debug import ExceptionReporter


class AdminEmailHandler(log.AdminEmailHandler):

    def emit(self, record):
        try:
            request = record.request
            subject = '%s (%s IP: %s): %s' % (record.levelname, (request.user if request.user else 'No user'),
                                              ('internal' if request.META.get('REMOTE_ADDR') in settings.INTERNAL_IPS else
                                               'EXTERNAL'), record.getMessage())
        except Exception:
            subject = '%s: %s' % (record.levelname, record.getMessage())
            request = None
        subject = self.format_subject(subject)

        # Since we add a nicely formatted traceback on our own, create a copy
        # of the log record without the exception data.
        no_exc_record = copy(record)
        no_exc_record.exc_info = None
        no_exc_record.exc_text = None

        if record.exc_info:
            exc_info = record.exc_info
        else:
            exc_info = (None, record.getMessage(), None)

        reporter = ExceptionReporter(request, is_email=True, *exc_info)
        message = "%s\n\n%s" % (self.format(no_exc_record), reporter.get_traceback_text())
        html_message = reporter.get_traceback_html() if self.include_html else None
        self.send_mail(subject, message, fail_silently=True, html_message=html_message)
