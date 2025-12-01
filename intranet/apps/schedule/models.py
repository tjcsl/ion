import datetime

from django.db import models
from django.utils import timezone

from ...settings.__init__ import ATTENDANCE_CODE_BUFFER


def shift_time(time: datetime.time, minutes: int) -> datetime.time:
    """Shifts the given time field by a certain number of minutes, with safeties: if shifting under 0,0,0 or past 23,59,59,
    it returns 0,0,0 or 23,59,59, respectively.
    Args:
        time: A datetime.time object
        minutes: Number of minutes (int)
    Returns:
        A datetime.time object which is the time argument shifted by minutes (if minutes is negative, shifts backwards)
    """
    today = datetime.datetime.today()
    if minutes < 0:
        t = datetime.time(0, -minutes, 0)
        if time < t:
            return datetime.time(0, 0, 0)
    else:
        delta = datetime.datetime.combine(today, datetime.time(23, 59, 59)) - datetime.datetime.combine(today, time)
        if minutes > delta.total_seconds() / 60:
            return datetime.time(23, 59, 59)
    dt = datetime.datetime.combine(today, time)
    return (dt + datetime.timedelta(minutes=minutes)).time()


class Time(models.Model):
    hour = models.IntegerField()
    minute = models.IntegerField()

    def __str__(self):
        minute = "0" + str(self.minute) if self.minute < 10 else self.minute
        return f"{self.hour}:{minute}"

    def str_12_hr(self):
        hour = self.hour if self.hour <= 12 else (self.hour - 12)
        minute = "0" + str(self.minute) if self.minute < 10 else self.minute
        return f"{hour}:{minute}"

    def date_obj(self, date):
        return datetime.datetime(date.year, date.month, date.day, self.hour, self.minute)

    class Meta:
        unique_together = ("hour", "minute")
        ordering = ("hour", "minute")


class Block(models.Model):
    name = models.CharField(max_length=100)
    start = models.ForeignKey("Time", related_name="blockstart", on_delete=models.CASCADE)
    end = models.ForeignKey("Time", related_name="blockend", on_delete=models.CASCADE)
    order = models.IntegerField(default=0)
    eighth_auto_open = models.TimeField(
        null=True, blank=True
    )  # time when attendance is opened for sch_acts with "auto" mode set, 11:59:59 if not eighth period
    eighth_auto_close = models.TimeField(null=True, blank=True)  # 00:00:00 if not eighth period

    def __str__(self):
        return f"{self.name}: {self.start} - {self.end}"

    def calculate_eighth_auto_times(self):
        """Generates the times when eighth-block code attendance opens and closes automatically."""
        if "8" in self.name:
            start = datetime.time(hour=self.start.hour, minute=self.start.minute)
            end = datetime.time(hour=self.end.hour, minute=self.end.minute)
            self.eighth_auto_open = shift_time(start, -ATTENDANCE_CODE_BUFFER)
            self.eighth_auto_close = shift_time(end, ATTENDANCE_CODE_BUFFER)
        else:
            self.eighth_auto_open = None
            self.eighth_auto_close = None

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.calculate_eighth_auto_times()
        super().save(update_fields=["eighth_auto_open", "eighth_auto_close"])

    class Meta:
        unique_together = ("order", "name", "start", "end")
        ordering = ("order", "name", "start", "end")


class CodeName(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class DayType(models.Model):
    name = models.CharField(max_length=100)
    codenames = models.ManyToManyField("CodeName", blank=True)
    special = models.BooleanField(default=False)
    blocks = models.ManyToManyField("Block", blank=True)

    def __str__(self):
        return self.name

    @property
    def class_name(self):
        n = self.name.lower()
        t = "other"

        if "blue day" in n or "mod blue" in n:
            t = "blue"

        if "red day" in n or "mod red" in n:
            t = "red"

        if "anchor day" in n or "mod anchor" in n:
            t = "anchor"

        if self.special:
            return f"day-type-{t} day-special"
        else:
            return f"day-type-{t}"

    @property
    def start_time(self) -> Time:
        """Returns Time the school day begins.
        Returns None if there are no blocks.

        Returns:
            The Time at which the school day starts, or None if there are no blocks.

        """
        first_block = self.blocks.first()
        return first_block.start if first_block is not None else None

    @property
    def end_time(self) -> Time:
        """Returns Time the school day ends.
        Returns None if there are no blocks.

        Returns:
            The Time at which the school day ends, or None if there are no blocks.

        """
        last_block = self.blocks.last()
        return last_block.end if last_block is not None else None

    @property
    def no_school(self) -> bool:
        """Returns True if no blocks are scheduled.

        Returns:
            Whether there are no blocks scheduled.

        """
        return not self.blocks.exists()

    class Meta:
        ordering = ("name",)


class DayManager(models.Manager):
    def get_future_days(self):
        """Return only future Day objects."""
        today = timezone.now().date()

        return Day.objects.filter(date__gte=today)

    def today(self):
        """Return the Day for the current day"""
        today = timezone.localdate()
        try:
            return Day.objects.get(date=today)
        except Day.DoesNotExist:
            return None


class Day(models.Model):
    objects = DayManager()
    date = models.DateField(unique=True)
    day_type = models.ForeignKey("DayType", on_delete=models.CASCADE)
    comment = models.CharField(max_length=1000, blank=True)

    @property
    def start_time(self):
        """Return time the school day begins"""
        return self.day_type.start_time

    @property
    def end_time(self):
        """Return time the school day ends"""
        return self.day_type.end_time

    def __str__(self):
        return f"{self.date}: {self.day_type}"

    class Meta:
        ordering = ("date",)
