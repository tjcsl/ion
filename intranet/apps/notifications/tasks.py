from celery import shared_task

from . import emails


email_send_task = shared_task(emails.email_send)
