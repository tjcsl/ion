import hashlib
import json

from django.conf import settings
from django.db import models
from push_notifications.models import WebPushDevice


class NotificationConfig(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    gcm_token = models.CharField(max_length=250, blank=True, null=True)
    gcm_time = models.DateTimeField(blank=True, null=True)
    gcm_optout = models.BooleanField(default=False)

    android_gcm_rand = models.CharField(max_length=100, blank=True, null=True)

    @property
    def gcm_token_sha256(self):
        return hashlib.sha256(self.gcm_token.encode()).hexdigest()

    def __str__(self):
        return str(self.user)


class GCMNotification(models.Model):
    multicast_id = models.CharField(max_length=250)
    num_success = models.IntegerField(default=0)
    num_failure = models.IntegerField(default=0)
    sent_data = models.CharField(max_length=10000)
    sent_to = models.ManyToManyField(NotificationConfig)
    time = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.multicast_id} at {self.time}"

    @property
    def data(self):
        json_data = json.loads(self.sent_data)
        if json_data and "data" in json_data:
            return json_data["data"]
        return {}


class UserPushNotificationPreferences(models.Model):
    """Represents a user's preferences for (Web)push notifications
    By default, subscribing to notifications enrolls the user for
    eighth absence and scheduling conflict (i.e. cancelled activity) notifications.
    Attributes:
        user
            The :class:`User<intranet.apps.users.models.User>` who has
            subscribed to notifications.
        eighth_reminder_notifications
            Whether the user wants to receive eighth period reminder
            notifications to sign up if they haven't already
            signed up within settings.PUSH_NOTIFICATIONS_EIGHTH_REMINDER_MINUTES
            minutes of the blocks locking
        eighth_waitlist_notifications
            Whether the user wants to receive notifications if using the
            waitlist. This is currently not in use (waitlist is disabled)
        glance_notifications
            Whether the user wants to receive their eighth period "glance"
            as a notification (it shows what blocks they've signed up for)
        announcement_notifications
            Whether the user wants to receive notifications when a new
            Ion announcement is posted
        poll_notifications
            Whether the user wants to receive a notification when a poll
            they can vote in opens
        bus_notifications
            Whether the user wants to receive notifications related to bus info
            i.e. when and where their bus arrives or if their bus is late
        is_subscribed
            Set to true if the user has one or more devices subscribed to Webpush;
            otherwise, false.
    """

    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="push_notification_preferences", on_delete=models.CASCADE)
    eighth_reminder_notifications = models.BooleanField("Eighth Period Reminder Notifications", default=True)
    eighth_waitlist_notifications = models.BooleanField("Eighth Period Waitlist Notifications", default=True)
    glance_notifications = models.BooleanField("Eighth Period Glance Notification", default=True)
    announcement_notifications = models.BooleanField("Announcement Notifications", default=True)
    poll_notifications = models.BooleanField("Poll Notifications", default=True)
    bus_notifications = models.BooleanField("Bus Notifications", default=True)

    # True if the user is subscribed to at least one device or more
    is_subscribed = models.BooleanField(default=False)

    def __str__(self):
        return str(self.user)


class WebPushNotification(models.Model):
    """This model is only used to store sent WebPushNotifications.
    If you are trying to send a notification, using the send notification
    functions located in intranet.apps.notifications.tasks
    Notifications sent from those functions are automatically added here
    to keep track of sent notifications' history
    """

    class Targets(models.TextChoices):
        USER = "user", "User"
        DEVICE = "device", "Single Device"
        DEVICE_QUERYSET = "device_queryset", "Device Queryset (Multiple Devices)"

    date_sent = models.DateTimeField(auto_now=True)
    target = models.CharField(max_length=15, choices=Targets.choices)

    user_sent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="notifications_user_sent")
    device_queryset_sent = models.ManyToManyField(WebPushDevice, blank=True)
    device_sent = models.ForeignKey(WebPushDevice, on_delete=models.SET_NULL, null=True, blank=True, related_name="notifications_device_sent")

    title = models.TextField()
    body = models.TextField()

    def __str__(self):
        return f"Notification sent to {self.target} at {self.date_sent} ({self.title})"
