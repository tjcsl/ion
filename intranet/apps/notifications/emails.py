# -*- coding: utf-8 -*-

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template

logger = logging.getLogger(__name__)


def email_send(text_template, html_template, data, subject, emails, headers=None):
    """
        Send an HTML/Plaintext email with the following fields.

        text_template: URL to a Django template for the text email's contents
        html_template: URL to a Django tempalte for the HTML email's contents
        data: The context to pass to the templates
        subject: The subject of the email
        emails: The addresses to send the email to
        headers: A dict of additional headers to send to the message

    """

    text = get_template(text_template)
    html = get_template(html_template)
    text_content = text.render(data)
    html_content = html.render(data)
    subject = settings.EMAIL_SUBJECT_PREFIX + subject
    headers = {} if headers is None else headers
    msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_FROM, emails, headers=headers)
    msg.attach_alternative(html_content, "text/html")
    logger.debug("Emailing {} to {}".format(subject, emails))
    msg.send()

    return msg


def email_send_bcc(text_template, html_template, data, subject, emails, headers=None):
    """
        Send an HTML/Plaintext email with the following fields.

        text_template: URL to a Django template for the text email's contents
        html_template: URL to a Django tempalte for the HTML email's contents
        data: The context to pass to the templates
        subject: The subject of the email
        emails: The addresses to send the email to
        headers: A dict of additional headers to send to the message

    """

    text = get_template(text_template)
    html = get_template(html_template)
    text_content = text.render(data)
    html_content = html.render(data)
    subject = settings.EMAIL_SUBJECT_PREFIX + subject
    headers = {} if headers is None else headers
    msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_FROM, [settings.EMAIL_FROM], headers=headers, bcc=emails)
    msg.attach_alternative(html_content, "text/html")
    logger.debug("Emailing {} to {}".format(subject, emails))
    msg.send()

    return msg
