import math

from django.conf import settings
from django.db import models
from django.utils import timezone

from intranet.apps.users.models import User


class PrintJob(models.Model):
    """Represents a submitted print job to Ion printing.

    Attributes:
        user (:obj:`User`): The user submitting the job.
        printer (str): The printer to run the job on.
        file (File): The file that the user submitted.
        page_range (str): The page range to print.
        time (:obj:`datetime.datetime`): The time the job
            was submitted.
        printed (bool): Whether the job was printed.
        num_pages (int): The number of pages in this job.
            This is calculated after converting the job.
        duplex (bool): Whether to print duplex.
        fit (bool): Whether to fit to page.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    printer = models.CharField(max_length=100)
    file = models.FileField(upload_to="printing/")
    page_range = models.CharField(blank=True, max_length=100)
    time = models.DateTimeField(auto_now_add=True)
    printed = models.BooleanField(default=False)
    num_pages = models.IntegerField(default=0)
    duplex = models.BooleanField(default=True, verbose_name="Double-sided")
    fit = models.BooleanField(default=False, verbose_name="Fit-to-page")

    def __str__(self):
        return f"{self.file} by {self.user} to {self.printer}"


class PrintingInfraction(models.Model):
    """
    Represents a infraction issued for printer misuse.

    Attributes
    ----------
        user (:obj:`Users`): The user who received the infraction.
        reason (str): The reason that the infraction was issued.
        date_issued (:obj:`datetime.datetime`): The time when the infraction was issued.
        active_until (:obj:`datetime.datetime`): The time when the infraction will become inactive.

    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="printing_infractions")
    reason = models.TextField()
    date_issued = models.DateTimeField(default=timezone.now)
    active_until = models.DateTimeField()

    def is_active(self):
        return timezone.now() < self.active_until

    def __str__(self):
        return f"Infraction({self.user}, {self.date_issued.date()})"

    class Meta:
        """
        Metadata configurations for PrintingInfraction.

        Attributes
        ----------
        ordering (list): The ordering of the list of printing infractions.

        """

        ordering = ["-date_issued"]


class PrintingBan(models.Model):
    """
    Represents a ban issued for printing misuse.

    Attributes
    ----------
        user (:obj:`Users`): The user who received the ban.
        reason (str): The reason that the ban was issued.
        date_issued (:obj:`datetime.datetime`): The time when the ban was issued.
        ban_reason_type (str): Whether the ban was issued manually or automatically.
        active_until (:obj:`datetime.datetime`): The time when the ban will become inactive.

    """

    BAN_REASON_AUTO = "auto"
    BAN_REASON_MANUAL = "manual"
    BAN_REASONS = [
        (BAN_REASON_AUTO, "Automatic (infraction threshold)"),
        (BAN_REASON_MANUAL, "Manual (admin issued)"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="printing_bans")
    reason = models.TextField()
    ban_reason_type = models.CharField(max_length=10, choices=BAN_REASONS, default=BAN_REASON_MANUAL)
    date_issued = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    triggering_infractions = models.ManyToManyField(PrintingInfraction, blank=True)

    def is_currently_active(self):
        if not self.is_active:
            return False
        if self.expires_at is None:
            return True
        return timezone.now() < self.expires_at

    def is_permanent(self):
        return self.expires_at is None

    def __str__(self):
        if self.is_permanent():
            expiry = "permanent"
        else:
            expiry = str(self.expires_at.date())
        return f"Ban({self.user}, until={expiry})"

    class Meta:
        """
        Metadata configurations for PrintingInfraction.

        Attributes
        ----------
        ordering (list): The ordering of the list of printing infractions.

        """

        ordering = ["-date_issued"]


# Formula for banning
# score < 3, no ban
# 3 <= score < 11, temp ban, days = round(e^(score * 0.5))
# score >= 12, perm ban (because the value would be longer than the school year) (I am assuming that the bans are supposed to be deactivated before the next school year)


def compute_ban_duration(score):
    if score >= 12:
        return None
    if score < 3:
        return 0
    else:
        return round(math.exp(score * 0.5))


def get_active_ban(user):
    return (
        PrintingBan.objects.filter(user=user, is_active=True)
        .filter(models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now()))
        .order_by("-date_issued")
        .first()
    )
