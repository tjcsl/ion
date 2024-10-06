import datetime
from typing import Dict

from intranet import settings
from intranet.apps.bus.tasks import push_bus_notifications
from intranet.apps.eighth.tasks import push_eighth_reminder_notifications, push_glance_notifications


def truncate_content(content: str) -> str:
    if len(content) > 200:
        return content[:200] + "..."
    return content


def truncate_title(title: str) -> str:
    if len(title) > 50:
        return title[:50] + "..."
    return title


def return_all_notification_schedules() -> Dict[str, Dict[str, datetime.datetime]]:
    schedules = {
        "Bus": {},
        "Eighth": {},
    }
    schedules["Bus"]["Bus location notification @ dismissal"] = push_bus_notifications(True, True)
    schedules["Eighth"][f"Sign up reminder before blocks lock @ {settings.PUSH_NOTIFICATIONS_EIGHTH_REMINDER_MINUTES} min before"] = (
        push_eighth_reminder_notifications(True, True)
    )
    schedules["Eighth"]["Glance notification @ eighth period start"] = push_glance_notifications(True, True)

    return schedules
