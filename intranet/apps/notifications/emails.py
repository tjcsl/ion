import logging
from typing import Collection, Mapping

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template

logger = logging.getLogger(__name__)


def email_send(
    text_template: str,
    html_template: str,
    data: Mapping[str, object],
    subject: str,
    emails: Collection[str],  # pylint: disable=unsubscriptable-object
    headers: Mapping[str, str] = None,  # pylint: disable=unsubscriptable-object
    bcc: bool = False,
    *,
    custom_logger: logging.Logger = None
) -> EmailMultiAlternatives:
    """Send an HTML/Plaintext email with the following fields.
    If we are not in production and settings.FORCE_EMAIL_SEND is not set, does not actually send the email

    Args:
        text_template: URL to a Django template for the text email's contents
        html_template: URL to a Django tempalte for the HTML email's contents
        data: The context to pass to the templates
        subject: The subject of the email
        emails: The addresses to send the email to
        headers: A dict of additional headers to send to the message
        custom_logger: An optional logger to use instead of the Django logger

    Returns:
        The email object that was created (and sent if we're in production or settings.FORCE_EMAIL_SEND is set)

    """

    logger = custom_logger if custom_logger is not None else globals()["logger"]  # pylint: disable=redefined-outer-name

    text = get_template(text_template)
    html = get_template(html_template)
    text_content = text.render(data)
    html_content = html.render(data)
    subject = settings.EMAIL_SUBJECT_PREFIX + subject
    headers = {} if headers is None else headers
    if bcc:
        msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_FROM, [settings.EMAIL_FROM], headers=headers, bcc=emails)
    else:
        msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_FROM, emails, headers=headers)
    msg.attach_alternative(html_content, "text/html")

    if not emails:
        logger.debug("Email list is empty; not sending")
        return msg

    logger.debug("Emailing %s to %s", subject, emails)

    # We only want to actually send emails if we are in production or explicitly force sending.
    if settings.PRODUCTION or settings.FORCE_EMAIL_SEND:
        msg.send()
    else:
        logger.debug("Refusing to email in non-production environments. To force email sending, enable settings.FORCE_EMAIL_SEND.")

    return msg
